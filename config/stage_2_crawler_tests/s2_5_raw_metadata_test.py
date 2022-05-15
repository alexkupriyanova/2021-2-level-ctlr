"""
Dataset validation
"""
import re
import json
import unittest

import pytest
import requests
from constants import ASSETS_PATH


class RawBasicDataValidator(unittest.TestCase):
    """
    Ensure collected data includes basic information
    """
    def setUp(self) -> None:
        # open and prepare texts
        self.texts = []
        for file_name in ASSETS_PATH.iterdir():
            if file_name.name.endswith("_raw.txt"):
                with file_name.open(encoding='utf-8') as file:
                    file = file.read()
                    print(file_name)
                    self.texts.append((int(file_name.name.split('_')[0]), file))
        self.texts = tuple(self.texts)

    @pytest.mark.mark4
    @pytest.mark.mark6
    @pytest.mark.mark8
    @pytest.mark.mark10
    @pytest.mark.stage_2_5_dataset_validation
    def test_validate_sort_raw(self):
        """
        Ensure raw files numeration is homogeneous
        """
        list_ids = [pair[0] for pair in self.texts]
        for i in range(1, len(list_ids)+1):
            self.assertTrue(i in list_ids,
                            msg="Articles ids are not homogeneous. "
                                "E.g. numbers are not from 1 to N")

    @pytest.mark.mark4
    @pytest.mark.mark6
    @pytest.mark.mark8
    @pytest.mark.mark10
    @pytest.mark.stage_2_5_dataset_validation
    def test_texts_are_not_empty(self):
        """
        Ensure text files are not empty
        """
        msg = "Text with ID: %s seems to be empty (less than 50 characters). " \
              "Check if you collected article correctly"
        for file_name in self.texts:
            self.assertTrue(len(file_name[1]) > 50,
                            msg=msg % file_name[0])


def check_title_in_html(title, html):
    split_markers = "&nbsp;|&#160;|&#32;|&#9248;|&#9248;" \
                    r"|&#xA0;|&#x20;|&#x2420;|&#x2423;|&#9251;|\s"
    split_title = re.split(split_markers, title)
    return all(chunk in html for chunk in split_title)


class RawMediumDataValidator(unittest.TestCase):
    """
    Ensure collected data includes extended information
    """
    def setUp(self) -> None:
        # check metadata is created under ./tmp/articles directory
        error_message = "Articles were not created in the ./tmp/articles " \
                        "directory after running scrapper.py. " \
                        "Check where you create articles"
        self.assertTrue(ASSETS_PATH.exists(), msg=error_message)

        # open and prepare metadata
        self.metadata = []
        for file_name in ASSETS_PATH.iterdir():
            if file_name.name.endswith(".json"):
                with file_name.open(encoding='utf-8') as file:
                    config = json.load(file)
                    self.metadata.append((config['id'], config))
        self.metadata = tuple(self.metadata)

    @pytest.mark.mark6
    @pytest.mark.mark8
    @pytest.mark.mark10
    @pytest.mark.stage_2_5_dataset_validation
    def test_validate_sort_metadata(self):
        """
        Ensure meta files are not empty
        """
        list_ids = [pair[0] for pair in self.metadata]
        for i in range(1, len(list_ids)+1):
            self.assertTrue(i in list_ids,
                            msg="Meta file ids are not homogeneous. "
                                "E.g. numbers are not from 1 to N")

    @pytest.mark.mark6
    @pytest.mark.mark8
    @pytest.mark.mark10
    @pytest.mark.stage_2_5_dataset_validation
    def test_validate_metadata_medium(self):
        """
        Ensure collected metadata is valid
        """
        # can i open this URL?
        for metadata in self.metadata:
            if metadata[1]['url'].endswith(".pdf"):
                continue
            msg = "Can not open URL: %s. Check how you collect URLs"
            self.assertTrue(requests.get(metadata[1]['url'], timeout = 60),
                            msg=msg % metadata[1]['url'])

            html_source = requests.get(metadata[1]['url'], timeout = 60).text
            msg = "Title is not found by specified in metadata " \
                  "URL %s. Check how you collect titles"
            self.assertTrue(check_title_in_html(metadata[1]['title'],
                                                html_source),
                            msg=msg % metadata[1]['url'])

            # author is presented? NOT FOUND otherwise?
            try:
                if isinstance(metadata[1]['author'], str):
                    self.assertTrue(metadata[1]['author'] in html_source)
                elif isinstance(metadata[1]['author'], list):
                    self.assertTrue(all(author in html_source
                                        for author in metadata[1]['author']))
                else:
                    error_message = f"Author field {metadata[1]['author']} has " \
                                    f"incorrect type. String or list are " \
                                    f"expected, {type(metadata[1]['author'])} " \
                                    f"is received."
                    raise TypeError(error_message)
            except AssertionError:
                message = f"Author field {metadata[1]['author']} " \
                          f"(url <{metadata[1]['url']}>) is incorrect. " \
                          "Collect author from the page or specify it " \
                          "with special keyword <NOT FOUND> " \
                          "if it is not presented at the page."
                self.assertEqual(metadata[1]['author'],
                                 'NOT FOUND',
                                 msg=message)


class RawAdvancedDataValidator(unittest.TestCase):
    """
    Ensure collected data includes all the required information
    """
    def setUp(self) -> None:
        # check metadata is created under ./tmp/articles directory
        error_message = "Articles were not created in the ./tmp/articles " \
                        "directory after running scrapper.py. " \
                        "Check where you create articles"
        self.assertTrue(ASSETS_PATH.exists(), msg=error_message)

        # datetime pattern
        self.data_pattern = r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d"

        # open and prepare metadata
        self.metadata = []
        for file_name in ASSETS_PATH.iterdir():
            if file_name.name.endswith(".json"):
                with file_name.open(encoding='utf-8') as file:
                    config = json.load(file)
                    self.metadata.append((config['id'], config))
        self.metadata = tuple(self.metadata)

    @pytest.mark.mark8
    @pytest.mark.mark10
    @pytest.mark.stage_2_5_dataset_validation
    def test_validate_metadata_advanced(self):
        """
        Ensure that collected data includes correct date and topics
        """
        for metadata in self.metadata:
            if metadata[1]['url'].endswith(".pdf"):
                continue

            html_source = requests.get(metadata[1]['url'], timeout = 60).text

            message = f"Date <{metadata[1]['date']}> do not match given " \
                      f"format <{self.data_pattern}> " \
                      f"(url <{metadata[1]['url']}>). " \
                      f"Check how you write dates."
            self.assertTrue(re.search(self.data_pattern,
                                      metadata[1]['date']),
                            msg=message)

            topics = metadata[1]['topics']
            if topics:
                for topic in topics:
                    message = f"Topics <{metadata[1]['topics']}> " \
                              f"(topic <{topic}>) for url " \
                              f"<{metadata[1]['url']}> are not found. " \
                              f"Check how you create topics."
                    self.assertTrue(topic in html_source, msg=message)


if __name__ == "__main__":
    unittest.main()
