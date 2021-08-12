from dataclasses import dataclass
from datetime import date
import json
from typing import List
import functools
import operator
import pandas as pd

# Class definitions for entity and relation types


@dataclass
class Entity:
    """
    Class for storing entity data.
    Valid types: PERSON, ORG, POSITION, PRONOUN
    """
    name: str
    type: str
    start_in_text: int
    end_in_text: int


@dataclass
class Relation:
    """
    Class for storing relation data.
    Valid types: WILL_HAVE_POSITION, IS_ENDING_POSITION, HAS_ONGOING_POSITION, HAD_POSITION, AT, WILL_JOIN, IS_LEAVING,
    IS_AT, HAD_POSITION_AT, HAS_PRONOUN, REPORTS_TO
    """
    entity_1: Entity
    entity_2: Entity
    type: str
    entry_date: date = None


@dataclass
class Story:
    '''
    Convenience class for stories. A story is defined as a list of relations, but we also group together the original
    text to add context.
    '''
    relations: List[Relation]
    text: str

    def extract_entities(self):
        '''
        Method to extract entities into a format that can be easily converted into a Pandas DataFrame.
        :return: A list of tuples where each tuple contains entity data.
        '''
        entities = []
        for relation in self.relations:
            entities.append(relation.entity_1)
            entities.append(relation.entity_2)
        output = [(entity.name, entity.type, entity.start_in_text, entity.end_in_text, self.text) for entity in entities]
        return output


def jsonl_to_list(jsonl_file_location):
    '''
    Reads a JSONL file and converts it into a list of JSON objects.
    :param jsonl_file_location: A string containing the path to a JSONL file.
    :return: A list of JSON objects.
    '''
    jsonl_file = open(jsonl_file_location, 'r')
    entries = []
    for line in jsonl_file:
        entries.append(json.loads(line))
    return entries


def parse_story(story_json):
    '''
    Parse the raw JSON describing a move story (produced by Prodigy) into a Story object
    :param story_json: Raw JSON describing a move story. Will be a single line of the JSONL file produced by prodigy.
    :return: An object of class Story
    '''
    relations = story_json['relations']
    text = story_json['text']
    new_relations = []
    for relation in relations:
        relation_type = relation['label']
        entity_1_json = relation['head_span']
        entity_2_json = relation['child_span']

        # Extract the name of Entity 1 from the text string and then construct a new Entity
        entity_1_name = text[entity_1_json['start']:entity_1_json['end']]
        entity_1 = Entity(name=entity_1_name,
                          type=entity_1_json['label'],
                          start_in_text=entity_1_json['start'],
                          end_in_text=entity_1_json['end'])

        # Same as above but for entity 2
        entity_2_name = text[entity_2_json['start']:entity_2_json['end']]
        entity_2 = Entity(name=entity_2_name,
                          type=entity_2_json['label'],
                          start_in_text=entity_2_json['start'],
                          end_in_text=entity_2_json['end'])

        # Build Relation object
        new_relation = Relation(entity_1, entity_2, relation_type)
        new_relations.append(new_relation)
    story = Story(new_relations, text)
    return story


# Build list of Story objects
file_location = '/Users/taylor/OneDrive - University of Edinburgh/Shared/Financial Networks Project/tagged_data/move_entries_rel.jsonl'
stories_json_list = jsonl_to_list(file_location)
parsed_stories = list(map(lambda x: parse_story(x), stories_json_list))

# Build CSV for Tod
entities = list(map(lambda x: x.extract_entities(), parsed_stories))
entities_reduced = functools.reduce(operator.iconcat, entities, [])
data = pd.DataFrame(entities_reduced, columns=["Entity_Name", "Type", "Start_Position", "End_Position",
                                               "Original_Text"])
# Drop duplicates
data_no_dups = data.drop_duplicates()
data_no_dups.to_csv("~/entities_new.csv")

