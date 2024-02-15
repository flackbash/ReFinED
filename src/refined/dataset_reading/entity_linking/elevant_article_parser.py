import json
import numpy as np
from typing import Dict, Optional, List, Tuple, Set


class EntityMention:
    def __init__(self,
                 span: Tuple[int, int],
                 recognized_by: Optional[str] = None,
                 entity_id: Optional[str] = None,
                 linked_by: Optional[str] = None,
                 candidates: Optional[Set[str]] = None,
                 referenced_span: Optional[Tuple[int, int]] = None,
                 contained: Optional[bool] = None):
        self.span = span
        self.recognized_by = recognized_by
        self.entity_id = entity_id
        self.linked_by = linked_by
        self.referenced_span = referenced_span
        self.candidates = candidates if candidates is not None else set()
        self.contained = contained

    def to_dict(self, evaluation_format: Optional[bool] = True) -> Dict:
        d = {"span": self.span}
        if self.entity_id is not None:
            d["id"] = self.entity_id
        if evaluation_format:
            if self.recognized_by is not None:
                d["recognized_by"] = self.recognized_by
            if self.linked_by is not None:
                d["linked_by"] = self.linked_by
            if self.referenced_span is not None:
                d["referenced_span"] = self.referenced_span
            if self.candidates is not None:
                d["candidates"] = sorted(self.candidates)
            if self.contained is not None:
                d["contained"] = self.contained
        return d

    def link(self, entity_id: str, linked_by: str):
        self.entity_id = entity_id
        self.linked_by = linked_by

    def is_linked(self) -> bool:
        return self.entity_id is not None

    def overlaps(self, span: Tuple[int, int]) -> bool:
        return self.span[0] < span[1] and self.span[1] > span[0]

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return str(self)

    def __lt__(self, other) -> bool:
        return tuple(self.span) < tuple(other.span)


def entity_mention_from_dict(data: Dict) -> EntityMention:
    return EntityMention(span=tuple(data["span"]),
                         recognized_by=data["recognized_by"] if "recognized_by" in data else None,
                         entity_id=data["id"] if "id" in data else None,
                         linked_by=data["linked_by"] if "linked_by" in data else None,
                         referenced_span=data["referenced_span"] if "referenced_span" in data else None,
                         candidates=set([ent_id for ent_id in data["candidates"]]) if "candidates" in data else None,
                         contained=data["contained"] if "contained" in data else None)


class Article:
    def __init__(self,
                 id: int,
                 title: str,
                 text: str,
                 hyperlinks: Optional[List[Tuple[Tuple[int, int], str]]] = None,
                 title_synonyms: Optional[List[Tuple[int, int]]] = None,
                 url: Optional[str] = None,
                 entity_mentions: Optional[List[EntityMention]] = None,
                 evaluation_span: Optional[Tuple[int, int]] = None,
                 sections: Optional[List[Tuple[Tuple[int, int], str]]] = None):
        self.id = id
        self.title = title
        self.text = text
        self.hyperlinks = hyperlinks if hyperlinks else []
        self.title_synonyms = title_synonyms if title_synonyms else []
        self.url = url
        self.entity_mentions = {}
        self.entity_coverage = None
        self.span_to_span_id = dict()
        self.spans = []
        self.add_entity_mentions(entity_mentions)
        self.evaluation_span = evaluation_span if evaluation_span is not None else (0, len(self.text))
        self.sections = sections

    def add_entity_mentions(self, entity_mentions: Optional[List[EntityMention]]):
        if entity_mentions is not None:
            for entity_mention in entity_mentions:
                self.entity_mentions[entity_mention.span] = entity_mention

                # Int ids are not zero based such that 0 indicates no entity in entity_coverage
                new_span_id = len(self.span_to_span_id) + 1
                self.span_to_span_id[entity_mention.span] = new_span_id
                self.spans.append(entity_mention.span)

        self._update_entity_coverage()

    def _update_entity_coverage(self):
        self.entity_coverage = np.zeros(len(self.text), dtype=int)
        if self.entity_mentions is not None:
            for span in self.entity_mentions:
                begin, end = span
                self.entity_coverage[begin:end] = self.span_to_span_id[span]


def article_from_dict(data: Dict) -> Article:
    # spans are saved as lists, but must be tuples
    hyperlinks = [(tuple(span), target) for span, target in data["hyperlinks"]] if "hyperlinks" in data else None
    title_synonyms = [tuple(span) for span in data["title_synonyms"]] if "title_synonyms" in data else None
    sections = [(tuple(span), title) for span, title in data["sections"]] if "sections" in data else None
    return Article(id=int(data["id"]),
                   title=data["title"],
                   text=data["text"],
                   hyperlinks=hyperlinks,
                   title_synonyms=title_synonyms,
                   url=data["url"] if "url" in data else None,
                   entity_mentions=[entity_mention_from_dict(entity_mention_dict) for entity_mention_dict in
                                    data["entity_mentions"]] if "entity_mentions" in data else None,
                   evaluation_span=data["evaluation_span"] if "evaluation_span" in data else None,
                   sections=sections)


def article_from_json(dump: str) -> Article:
    return article_from_dict(json.loads(dump))
