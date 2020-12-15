import logging
from graphviz import Digraph

logging.basicConfig(level=logging.DEBUG)


class Graph:
    def __init__(self, theorem):
        self.theorem = theorem
        self.premise = []
        self.hypothesis = []
        self.entities = dict()
        self.events = dict()
        self.unmatched_entities = dict()
        self.unmatched_events = dict()
        self.prem_pred = dict()
        self.subgoal_pred = []
        return

    def addEntity(self, name, is_unified=True):
        assert name not in self.entities
        if is_unified:
            self.entities[name] = Entity(name)
        else:
            self.unmatched_entities[name] = Entity(name)
        return

    def addEvent(self, name, is_unified=True):
        assert name not in self.events
        if is_unified:
            self.events[name] = Event(name)
        else:
            self.unmatched_events[name] = Event(name)
        return

    def getEntity(self, name, is_unified=True):
        if is_unified:
            return self.entities[name]
        else:
            return self.unmatched_entities[name]

    def getEvent(self, name, is_unified=True):
        if is_unified:
            return self.events[name]
        else:
            return self.unmatched_events[name]

    def getE(self, name, is_unified=True):
        if is_unified:
            if name in self.entities:
                return self.entities[name]
            elif name in self.events:
                return self.events[name]
            else:
                raise ValueError(f"{name} is not found in the graph")
        else:
            if name in self.unmatched_entities:
                return self.unmatched_entities[name]
            elif name in self.unmatched_events:
                return self.unmatched_events[name]
            else:
                raise ValueError(f"{name} is not found in the graph")

    def setSemanticRole(self, entity_name):
        relation, event_name = entity_name.split(" ")
        relation = relation.lower()
        event = self.getEvent(event_name)
        assert not hasattr(event, relation)
        entity = self.getEntity(entity_name)
        setattr(event, relation, entity)
        return

    def addEs(self, type_lines):
        for line in type_lines:
            var, typ = line.split(" : ")
            if typ == "Entity":
                self.addEntity(var)
            elif typ == "Event":
                self.addEvent(var)
            else:
                raise ValueError("Type should be Entity or Event")

    def addPremise(self, premise_lines):
        logging.debug(premise_lines)
        type_lines, pred_lines = seperate_lines(premise_lines)
        self.addEs(type_lines)

        # pos surf info
        tokens = self.theorem.doc.xpath('./sentences/sentence[1]/tokens')[0]
        d = dict()
        for tok in tokens:
            base, pos, surf = get_attrs(tok)
            d[base] = pos, surf
            self.premise.append(surf)

        # add preds
        for line in pred_lines:

            H, body = line.split(" : ")
            pred_name = clean_pred_name(body)
            args = body.split()[1:]

            # process semantic role
            args = handleSemanticRoleArgs(args)
            args2 = []
            for a in args:
                if isSemanticRole(a) and a not in self.entities:
                    self.addEntity(a)
                    self.setSemanticRole(a)
                args2.append(self.getE(a))

            pos, surf = d[pred_name]
            self.prem_pred[pred_name] = Predicate(pred_name, args2, pos, surf)
        return

    def addSubgoals(self, subgoal_line):
        logging.debug(subgoal_line)
        tokens = self.theorem.doc.xpath('./sentences/sentence[2]/tokens')[0]
        d = dict()
        for tok in tokens:
            base, pos, surf = get_attrs(tok)
            d[base] = pos, surf
            self.hypothesis.append(base)

        for goal in subgoal_line:
            if "=" not in goal:
                pred_name = goal.split()[0]
                pred_name = clean_pred_name(pred_name)
                args = goal.split()[1:]
                if len(args) == 0:
                    breakpoint()
                args = handleSemanticRoleArgs(args)
                args = self.handleUnunifiedE(args)
                pos, surf = d[pred_name]
                p = Predicate(pred_name, args, pos, surf)
                self.subgoal_pred.append(p)
            else:
                print("TODO: = in goal")
                breakpoint()
        return

    def handleUnunifiedE(self, args):
        result = []
        for a in args:
            if a.startswith("?x") or a.startswith("?y") or a.startswith("?z"):
                if a not in self.unmatched_entities:
                    self.addEntity(a, is_unified=False)
                result.append(self.getEntity(a, is_unified=False))
            elif a.startswith("?e"):
                if a not in self.unmatched_events:
                    self.addEvent(a, is_unified=False)
                result.append(self.getEvent(a, is_unified=False))
            else:
                result.append(self.getE(a))
        return result

    def create_readable_subgoals(self):
        readable_subgoals = []
        created_axioms = []
        for pred in self.subgoal_pred:
            if pred.is_unified():
                if pred.is_ox():
                    readable_sg, axiom = self.from_ox(pred)
                elif pred.is_oe():
                    readable_sg, axiom = self.from_oe(pred)
                else:
                    assert pred.is_tp()
                    readable_sg, axiom = self.from_tp(pred)
            else:
                if pred.is_tp():
                    readable_sg, axiom = self.from_tp_ununified(pred)
                else:
                    continue
            readable_subgoals.append(readable_sg)
            created_axioms.append(axiom)
            logging.debug((readable_sg, axiom))
        return readable_subgoals, created_axioms

    def from_ox(self, subgoal):
        logging.debug(
            f"readable subgoal from one place entity pred: {subgoal.name}")
        e = subgoal.args[0]
        subj = e.getNoun()

        if subgoal.pos == 'IN':
            print("One place IN taking x??")
            breakpoint()

        copula = selectCopula(subj)
        det = selectDeterminer(subgoal)

        if subgoal.pos == "CD":
            readable_sg = f"There are {subgoal.surf} {subj.surf}"
        else:
            readable_sg = f'The {subj.surf} {copula}{det}{subgoal.surf}'
        axiom = f"Axiom {subgoal.surf} : {subgoal.name}({e.name})"

        return readable_sg, axiom

    def from_oe(self, subgoal):
        logging.debug(
            f"readable subgoal from one place event pred: {subgoal.name}")
        e = subgoal.args[0]

        # Get subject and select copula
        subj = e.subj.getNoun()
        copula = selectCopula(subj)
        det = selectDeterminer(subgoal)

        # Get verb phrase and create result
        vp = e.getVP()
        if subgoal.pos.startswith('V'):
            readable_sg = f'The {subj.surf} {copula} {vp}'
        elif subgoal.pos.startswith('RB'):
            readable_sg = f'The {subj.surf} {copula} {vp} {subgoal.surf}'
        elif subgoal.pos.startswith('N'):
            det = selectDeterminer(subgoal)
            readable_sg = f'The {subj.surf} {copula}{det}{subgoal.surf}'
        else:
            raise ValueError()

        axiom = f"Axiom {vp} : {subgoal.name}({e.name})"
        return readable_sg, axiom

    def from_tp(self, subgoal):
        logging.debug(
            f"readable subgoal from two place preposition pred: {subgoal.name}"
        )
        args = subgoal.args
        if args[0].is_unified():
            event = args[0]
            e = args[1]
        else:
            event = args[1]
            e = args[0]
        subj = event.subj.getNoun()
        arg_pred = e.getContentWord()
        copula = selectCopula(subj)
        det = selectDeterminer(arg_pred)
        readable_sg = f'The {subj.surf} {copula} {subgoal.surf}{det}{arg_pred.surf}'
        axiom = f"Axiom {subgoal.name} : {subgoal.name}({event.name},{e.name})"
        return readable_sg, axiom

    def from_tp_ununified(self, subgoal):
        logging.debug(
            f"readable subgoal from un-unified two place preposition pred: {subgoal.name}"
        )
        args = subgoal.args
        if args[0].is_unified():
            event = args[0]
            ununified = args[1]
        else:
            event = args[1]
            ununified = args[0]
        subj = event.subj.getNoun()
        arg_pred = ununified.getContentWord()
        copula = selectCopula(subj)
        det = selectDeterminer(arg_pred)
        readable_sg = f'The {subj.surf} {copula} {subgoal.surf}{det}{arg_pred.surf}'
        axiom = f"Axiom {subgoal.name} : {subgoal.name}({event.name},{ununified.getNewName()})"
        if isinstance(ununified, Entity):
            axiom += ""
        elif isinstance(ununified, Event):
            axiom += ""
        else:
            raise ValueError("ununified should be entity or event")
        return readable_sg, axiom

    def visualize(self, with_subgoal=True):
        g = Digraph('G', filename='graph.gv', engine='sfdp')

        for e in self.entities.values():
            if e.subgoal:
                if not with_subgoal:
                    continue
                else:
                    g.node(e.name, color='lightpink', style='filled')
                    if e.matched is not None:
                        g.edge(e.name, e.matched.name, label='unified')
            else:
                g.node(e.name,
                       shape='box',
                       color='aquamarine2',
                       style='filled')

        for e in self.events.values():

            if e.subgoal:
                if not with_subgoal:
                    continue
                else:
                    g.node(e.name, color='lightpink', style='filled')
                    if e.matched is not None:
                        g.edge(e.name, e.matched.name, label='unified')

            else:
                g.node(e.name,
                       shape='box',
                       color='aquamarine2',
                       style='filled')

            for sr in ['subj', 'acc', 'dat']:
                if hasattr(e, sr):
                    ent = getattr(e, sr)
                    g.edge(e.name, ent.name, label=sr)

        for p in self.predicate.values():
            g.node(p.name)
            for e in p.args:
                g.edge(p.name, e.name)
        g.view()
        return


class Predicate():
    def __init__(self, name, args, pos, surf):
        self.name = name
        self.surf = surf
        self.pos = pos
        self.args = []
        self.addArgs(args)

    def addEntity(self, ent):
        assert isinstance(
            ent,
            Entity), f'non entity {ent} tried to be added to pred {self.name}'
        self.args.append(ent)
        ent.addPred(self)
        return

    def addEvent(self, evt):
        assert isinstance(
            evt,
            Event), f'non event {evt} tried to be added to pred {self.name}'
        self.args.append(evt)
        evt.addPred(self)
        return

    def getEntity(self):
        for e in self.args:
            if isinstance(e, Entity):
                return e
        return None

    def getEvent(self):
        for e in self.args:
            if isinstance(e, Event):
                return e
        return None

    def addArgs(self, arg):
        assert isinstance(arg, list)
        for a in arg:
            if isinstance(a, Entity):
                self.addEntity(a)
            elif isinstance(a, Event):
                self.addEvent(a)
            else:
                raise ValueError("Arg should be Entity or Event")
        return

    def is_ox(self):
        return len(self.args) == 1 and isinstance(self.args[0], Entity)

    def is_oe(self):
        return len(self.args) == 1 and isinstance(self.args[0], Event)

    def is_tp(self):
        return len(self.args) == 2

    def is_unified(self):
        return all([e.is_unified() for e in self.args])


class Variable:
    def __init__(self, name):
        self.name = name
        self.predicates = []
        return

    def addPred(self, p):
        assert isinstance(p, Predicate)
        self.predicates.append(p)
        return

    def is_unified(self):
        return not self.name.startswith("?")

    def getNewName(self):
        assert not self.is_unified()
        return self.name.lstrip("?")

    def getContentWord(self):
        for p in self.predicates:
            if not p.pos == "IN":
                return p
        return


class Entity(Variable):
    def __init__(self, name):
        super().__init__(name)
        return

    def getNoun(self):
        for p in self.predicates:
            if p.pos.startswith('N'):
                return p
        return None

    def getProp(self):
        for p in self.predicates:
            if p.pos == 'IN':
                return p
        return


class Event(Variable):
    def __init__(self, name):
        super().__init__(name)
        return

    def getVerb(self):
        for p in self.predicates:
            if p.pos.startswith('V'):
                return p
        return None

    def getVP(self):
        verb = self.getVerb()
        result = verb.surf
        if hasattr(verb, 'acc'):
            acc = verb.acc
            det = selectDeterminer(acc)
            result += f'{det} {acc.surf}'
            if hasattr(verb, 'dat'):
                dat = verb.dat
                det = selectDeterminer(dat)
                result += f'to {det} {dat.surf}'
        return result


def progressive(p):
    # TODO change this to spacy or nltk or something
    p.name = p.name.split('_')[0]
    if p.name.endswith('ing'):
        return p
    if p.name.endswith('t'):
        p.name = p.name + 't'
    elif p.name.endswith('e'):
        p.name = p.name.rstrip('e')
    p.name = p.name + 'ing'
    return p


def seperate_lines(premise_lines):
    type_lines = []
    pred_lines = []
    for line in premise_lines:
        if not line.startswith("H"):
            type_lines.append(line)
        elif line.endswith("True"):
            continue
        else:
            pred_lines.append(line)
    return type_lines, pred_lines


def get_attrs(tok):
    base = tok.attrib.get('base')
    pos = tok.attrib.get('pos')
    surf = tok.attrib.get('surf')
    return base, pos, surf


def clean_pred_name(x):
    pred_name = x.split()[0].lstrip("_")
    if "_" in pred_name:
        pred_name = pred_name.split("_")[0]
    return pred_name


def handleSemanticRoleArgs(args):
    if len(args) == 1:
        return args
    elif args[0].startswith("("):
        if len(args) == 2:
            return [merge(args[0], args[1])]
        elif len(args) == 3:
            return [merge(args[0], args[1]), args[2]]
        elif len(args) >= 4:
            breakpoint()
    elif args[1].startswith("("):
        if len(args) == 3:
            return [args[0], merge(args[1], args[2])]
        elif len(args) >= 4:
            breakpoint()
    else:
        return args


def merge(x, y):
    return f"{x} {y}".strip("()")


def isSemanticRole(a):
    return a.startswith("Subj") or a.startswith("Acc") or a.startswith("Dat")


def selectCopula(x):
    if x.pos in {'NN', 'NNP'}:
        return 'is'
    else:
        return 'are'


def selectDeterminer(x):
    if x.pos in {'NN', 'NNP'}:
        return " a "
    else:
        return ' '
