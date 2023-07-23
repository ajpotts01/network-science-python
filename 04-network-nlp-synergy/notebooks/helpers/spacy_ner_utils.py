import requests

import pandas as pd
import spacy
from spacy import Language


# AJP utils
def init_spacy() -> Language:
    nlp: Language = spacy.load("en_core_web_md")

    return nlp


def get_data(url: str) -> str:
    text_output: str = requests.get(url=url).text
    return text_output


def clean_data(text_input: str, start_text: str, end_text: str = "THE END") -> str:
    CHR_SPACE: str = " "
    CHR_APOST: str = "â\x80\x99"  # '
    CHR_SDQUOT: str = "â\x80\x9c"  # "
    CHR_DDQUOT: str = "â\x80\x9d"  # ""
    CHR_MISC: str = "â\x80\x94"  # Not sure what this is but it gets replaced by a space

    index_start: int = text_input.index(start_text)
    index_end: int = text_input.rindex(end_text)
    text_output: str = (
        text_input[index_start:index_end]
        .replace("\r", CHR_SPACE)
        .replace("\n", CHR_SPACE)
        .replace(CHR_APOST, "'")
        .replace(CHR_SDQUOT, '"')  # lol
        .replace(
            CHR_DDQUOT, '"'
        )  # The book replaces this char with "" so that thoughts and dialog plus "he said" etc. get captured as one sentence
        .replace(CHR_MISC, CHR_SPACE)
    )

    return text_output


def remove_char_from_entity(text_entity: str, char_to_remove: str) -> str:
    if char_to_remove in text_entity:
        start_index: int = text_entity.index(char_to_remove)
        text_entity_cleaned: str = text_entity[:start_index]
        return text_entity_cleaned

    return text_entity


def clean_entity(text_entity: str) -> str:
    text_output: str = text_entity.strip()
    text_output = remove_char_from_entity(text_entity=text_output, char_to_remove="'s")

    return text_output


def extract_entities_from_sentence(
    nlp: Language, sentence: spacy.tokens.span.Span, desired_tags: list[str]
) -> list[str]:
    sentence_doc = nlp(sentence.text)

    entities: list[str] = [
        clean_entity(next_entity.text)
        for next_entity in sentence_doc.ents
        if next_entity.label_ in desired_tags
    ]
    entities = list(filter(lambda x: x != "", entities))

    return list(set(entities))


def extract_entities(
    nlp: Language, sentences_input: list[str], desired_tags: list[str]
) -> list[str]:
    # Filtered on desired_tag

    entities: list[str] = [
        extract_entities_from_sentence(
            nlp=nlp, sentence=next_sentence, desired_tags=desired_tags
        )
        for next_sentence in sentences_input
    ]

    entities = list(filter(lambda x: len(x) > 1, entities))

    return entities


def get_book_entities(
    url_book: str, start_text: str, end_text: str = "THE END"
) -> list[str]:
    nlp: Language = init_spacy()

    # Step 1: Get book data
    text_book: str = get_data(url=url_book)
    text_cleaned: str = clean_data(
        text_input=text_book, start_text=start_text, end_text=end_text
    )

    doc = nlp(text=text_cleaned)

    # Step 2: Get tags
    sentences: list[str] = list(doc.sents)

    entities: list[list[str]] = extract_entities(
        nlp=nlp, sentences_input=sentences, desired_tags=["PERSON", "ORG", "GPE"]
    )

    return entities


def create_network_data(entities: list[list[str]]) -> pd.DataFrame:
    """
    It is assumed in this case that the first entity in a list of entities is the source, and all subsequent entities are targets.
    """

    # Sources needs to be the same length as targets - so duplicate items across the list comprehension
    # https://stackoverflow.com/a/38054158
    sources: list[str] = [row[0] for row in entities for _ in range(len(row) - 1)]

    # https://stackoverflow.com/questions/25674169/how-does-the-list-comprehension-to-flatten-a-python-list-work
    # To figure this out on your own:
    # Write a nested loop way of doing this
    # e.g.
    # targets = []
    # for ent in entities:
    #     for sub_ent in ent[1:]:
    #         targets.append(sub_ent)
    # Then write the corresponding list comprehension from left to right.
    # It starts with the thing you'd append to the list, then you write the two for loops in sequence.
    targets: list[str] = [sub_ent for ent in entities for sub_ent in ent[1:]]

    # Create the relationship from source -> target with Pandas
    df_network_data: pd.DataFrame = pd.DataFrame(
        data=dict(source=sources, target=targets)
    )

    return df_network_data


# DK utils
def extract_entities_dk(text: str):
    nlp: Language = init_spacy()

    doc = nlp(text)
    sentences = list(doc.sents)
    entities = []
    for sentence in sentences:
        sentence_entities = []
        sent_doc = nlp(sentence.text)
        for ent in sent_doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE"]:
                entity = ent.text.strip()
                if "'s" in entity:
                    cutoff = entity.index("'s")
                    entity = entity[:cutoff]
                if entity != "":
                    sentence_entities.append(entity)
        sentence_entities = list(set(sentence_entities))
        if len(sentence_entities) > 1:
            entities.append(sentence_entities)
    return entities


def get_book_entities_dk(url_book: str, start_text: str, end_text: str) -> list[str]:
    # Step 1: Get book data
    text_book: str = get_data(url=url_book)
    text_cleaned: str = clean_data(
        text_input=text_book, start_text=start_text, end_text=end_text
    )

    entities: list[list[str]] = extract_entities_dk(text=text_cleaned)

    return entities


def test_ajp_vs_dk_entities(ent_ajp: list[list[str]], ent_dk: list[list[str]]):
    overall_match: bool = True

    assert len(ent_ajp) == len(ent_dk)
    for next_index in range(len(ent_ajp)):
        print(f"{ent_ajp[next_index]=}")
        print(f"{ent_dk[next_index]=}")
        current_match = ent_dk[next_index] == ent_ajp[next_index]
        print(f"Match: {current_match}")
        overall_match = overall_match and current_match

    print(f"Overall match: {overall_match}")
