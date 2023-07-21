import json
import os
from pathlib import Path
from re import L
from tempfile import TemporaryDirectory
from unittest import TestCase

import smart_open

from dolma.core.runtime import (
    _make_paths_from_prefix,
    _make_paths_from_substitution,
    create_and_run_tagger,
)

LOCAL_DATA = Path(__file__).parent.parent / "data"


class TestRuntimeUtilities(TestCase):
    # def test_make_paths_from_substitution(self):
    #     paths = [
    #         "s3://bucket/common-crawl/documents/cc_*/*.json.gz",
    #         "/local/path/to/documents/train/*",
    #     ]
    #     new_paths = _make_paths_from_substitution(
    #         paths=paths,
    #         find="documents",
    #         replace="attributes",
    #     )
    #     self.assertEqual(new_paths, ["s3://bucket/common-crawl/attributes", "/local/path/to/attributes/train"])

    # def test_make_paths_from_prefix(self):
    #     paths = [
    #         "s3://bucket/common-crawl/documents/cc_head/*.json.gz",
    #         "s3://bucket/common-crawl/documents/cc_middle/*.json.gz",
    #         "s3://bucket/common-crawl/documents/cc_tail/*.json.gz",
    #     ]
    #     new_paths = _make_paths_from_prefix(
    #         paths=paths,
    #         prefix="s3://bucket/common-crawl/attributes/",
    #     )
    #     self.assertEqual(
    #         new_paths,
    #         [
    #             "s3://bucket/common-crawl/attributes/cc_head",
    #             "s3://bucket/common-crawl/attributes/cc_middle",
    #             "s3://bucket/common-crawl/attributes/cc_tail",
    #         ],
    #     )

    #     paths = [
    #         "s3://bucket/common-crawl/documents/*.json.gz",
    #         "s3://bucket2/c4/documents/**/data/*.json.gz",
    #     ]
    #     new_paths = _make_paths_from_prefix(
    #         paths=paths,
    #         prefix="/local/path/",
    #     )
    #     self.assertEqual(
    #         new_paths,
    #         [
    #             "/local/path/bucket/common-crawl/documents",
    #             "/local/path/bucket2/c4/documents",
    #         ],
    #     )

    def test_runtime_e2e(self):
        documents_path = f"{LOCAL_DATA}/provided/documents/000.json.gz"
        experiment_name = "test"
        taggers = ["c4_v1"]

        with TemporaryDirectory() as temp_dir:
            create_and_run_tagger(
                documents=[documents_path],
                destination=temp_dir,
                taggers=taggers,
                experiment=experiment_name,
                debug=True,
            )
            destination_file = os.path.join(temp_dir, experiment_name, "000.json.gz")
            self.assertTrue(os.path.exists(destination_file))

            with smart_open.open(documents_path, "rt") as f:
                document = [json.loads(ln) for ln in f]

            with smart_open.open(destination_file, "rt") as f:
                attributes = [json.loads(ln) for ln in f]

        self.assertEqual(len(document), len(attributes))

        for d, a in zip(document, attributes):
            self.assertEqual(d["id"], a["id"])
            self.assertTrue(sorted(a.keys()), ["attributes", "id", "source"])

            for key, value in a["attributes"].items():
                parts = key.split("__")
                self.assertEqual(len(parts), 3)
                self.assertEqual(parts[0], experiment_name)
                self.assertTrue(parts[1] in taggers)

                for elem in value:
                    self.assertEqual(len(elem), 3)
                    self.assertTrue(isinstance(elem[0], int))
                    self.assertTrue(isinstance(elem[1], int))
                    self.assertTrue(isinstance(elem[2], float))

                if len(value) == 1:
                    self.assertEqual(value[0][0], 0)
                    self.assertEqual(value[0][1], len(d["text"]))
