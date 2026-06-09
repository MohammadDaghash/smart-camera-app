import json
import threading
from datetime import datetime, timezone

import numpy as np

from app.utils.logging import logger


class FaceIdentityStore:
    def __init__(self, path, known_threshold, anonymous_threshold):
        self.path = path
        self.known_threshold = known_threshold
        self.anonymous_threshold = anonymous_threshold
        self.lock = threading.RLock()
        self.data = self._load()

    def _empty_data(self):
        return {
            "version": 1,
            "next_anonymous_number": 1,
            "identities": [],
        }

    def _load(self):
        if not self.path.exists():
            logger.info("No local face identity store found yet: %s", self.path)
            return self._empty_data()

        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception as error:
            logger.warning("Could not load face identity store %s: %s", self.path, error)
            return self._empty_data()

        data.setdefault("version", 1)
        data.setdefault("next_anonymous_number", 1)
        data.setdefault("identities", [])
        data["next_anonymous_number"] = max(
            int(data["next_anonymous_number"]),
            self._next_number_from_existing_identities(data["identities"]),
        )
        logger.info("Loaded %s local face identity record(s)", len(data["identities"]))
        return data

    def _next_number_from_existing_identities(self, identities):
        highest_number = 0

        for identity in identities:
            identity_id = identity.get("id", "")

            if not identity_id.startswith("anonymous-"):
                continue

            try:
                highest_number = max(highest_number, int(identity_id.split("-", 1)[1]))
            except ValueError:
                continue

        return highest_number + 1

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2)
            file.write("\n")

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _normalize_embedding(self, embedding):
        embedding = np.asarray(embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding)

        if norm == 0:
            return None

        return embedding / norm

    def _identity_embedding(self, identity):
        embedding = identity.get("embedding")

        if embedding is None:
            return None

        return self._normalize_embedding(embedding)

    def _score(self, first_embedding, second_embedding):
        return float(np.dot(first_embedding, second_embedding))

    def _public_identity(self, identity):
        return {
            "id": identity["id"],
            "label": identity["label"],
            "name": identity.get("name"),
            "status": identity["status"],
            "match_count": identity.get("match_count", 0),
            "created_at": identity.get("created_at"),
            "updated_at": identity.get("updated_at"),
        }

    def list_identities(self):
        with self.lock:
            identities = sorted(
                self.data["identities"],
                key=lambda identity: (identity["status"], identity["label"]),
            )
            return [self._public_identity(identity) for identity in identities]

    def _find_best_identity(self, embedding, status):
        best_identity = None
        best_score = 0.0

        for identity in self.data["identities"]:
            if identity.get("status") != status:
                continue

            identity_embedding = self._identity_embedding(identity)

            if identity_embedding is None:
                continue

            score = self._score(embedding, identity_embedding)

            if score > best_score:
                best_score = score
                best_identity = identity

        return best_identity, best_score

    def match_promoted_identity(self, embedding):
        embedding = self._normalize_embedding(embedding)

        if embedding is None:
            return None, 0.0

        with self.lock:
            identity, score = self._find_best_identity(embedding, "known")

            if identity is not None and score >= self.known_threshold:
                return identity["label"], score

        return None, score

    def match_or_create_anonymous_identity(self, embedding):
        embedding = self._normalize_embedding(embedding)

        if embedding is None:
            return "Anonymous", 0.0

        with self.lock:
            identity, score = self._find_best_identity(embedding, "anonymous")

            if identity is not None and score >= self.anonymous_threshold:
                self._record_match(identity, embedding)
                return identity["label"], score

            identity = self._create_anonymous_identity(embedding)
            return identity["label"], 1.0

    def _record_match(self, identity, embedding):
        match_count = int(identity.get("match_count", 0)) + 1
        identity["match_count"] = match_count
        identity["updated_at"] = self._now()

        current_embedding = self._identity_embedding(identity)

        if current_embedding is not None:
            weight = min(match_count, 20)
            averaged_embedding = self._normalize_embedding(
                (current_embedding * weight) + embedding
            )

            if averaged_embedding is not None:
                identity["embedding"] = averaged_embedding.tolist()

        if match_count % 30 == 0:
            self._save()

    def _create_anonymous_identity(self, embedding):
        anonymous_number = int(self.data.get("next_anonymous_number", 1))
        label = f"Anonymous {anonymous_number}"
        now = self._now()

        identity = {
            "id": f"anonymous-{anonymous_number}",
            "label": label,
            "name": None,
            "status": "anonymous",
            "embedding": embedding.tolist(),
            "match_count": 1,
            "created_at": now,
            "updated_at": now,
        }

        self.data["identities"].append(identity)
        self.data["next_anonymous_number"] = anonymous_number + 1
        self._save()
        logger.info("Created local anonymous identity: %s", label)
        return identity

    def promote_identity(self, identity_id, name):
        clean_name = " ".join(name.strip().split())

        if not clean_name:
            raise ValueError("Name is required")

        with self.lock:
            for identity in self.data["identities"]:
                if identity["id"] != identity_id:
                    continue

                if identity["status"] != "anonymous":
                    raise ValueError("Only anonymous identities can be promoted")

                old_label = identity["label"]
                identity["status"] = "known"
                identity["name"] = clean_name
                identity["label"] = clean_name
                identity["updated_at"] = self._now()
                self._save()
                logger.info("Promoted %s to known identity: %s", old_label, clean_name)
                return self._public_identity(identity)

        raise KeyError(identity_id)
