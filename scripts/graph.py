from graphviz import Digraph


class Graph:
    def __init__(self):
        self.entities = dict()
        self.events = dict()
        self.predicate = dict()

    def addPred(self, i, name, pos, arg, subgoal):
        if name in self.predicate:
            name = f'{name}_2'  # fix this
        pred = Predicate(i, name, pos, arg, subgoal, self)
        self.predicate[pred.name] = pred
        return

    def addRelation(self, event, entity, name):

        unmatched = entity.startswith('?')
        if unmatched:
            entity = entity.lstrip('?')

        t_e, i_e = parse(event)
        t_x, i_x = parse(entity)

        if unmatched:
            i_x += 1000

        event = self.events[i_e]
        entity = self.entities[i_x]
        self.events[event.i].addRelation(entity, name)

        if event.matched_by is not None:
            if entity.i + 1000 in self.entities:
                entity = self.entities[entity.i + 1000]
            else:
                entity = self.entities[entity.i]
            self.events[event.matched_by.i].addRelation(entity, name)
        return

    def addEntity(self, e):
        assert isinstance(e, Entity) and e.i not in self.entities
        self.entities[e.i] = e
        return

    def addEvent(self, e):
        assert isinstance(e, Event) and e.i not in self.events
        self.events[e.i] = e
        return

    def create_axioms(self):
        result = []
        result += self.from_matched_entities()
        result += self.from_matched_events()
        return result

    def from_matched_entities(self):
        result = []
        e_list = [e for e in self.entities.values() if e.subgoal and e.matched]
        for e in e_list:
            if e.matched.get_pred_str() == e.get_pred_str():
                # case only prop is attached
                continue
            axiom = f'The {e.matched.get_pred_str()} is {e.get_pred_str(add_det=True)}'
            result.append(axiom)
        return result

    def from_matched_events(self):
        result = []
        e_list = [e for e in self.events.values() if e.subgoal and e.matched]
        for e in e_list:
            subject = e.matched.subj.get_pred_str()
            verb = e.get_pred_str(prog=True)
            prop = e.get_prop_str()
            axiom = f'The {subject} is {verb} {prop}'
            result.append(axiom)
        return result

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
            for e in p.arg:
                g.edge(p.name, e.name)
        g.view()
        return


class Predicate():
    def __init__(self, i, name, pos, arg, subgoal, graph):
        self.i = i
        self.name = name
        self.pos = pos
        self.graph = graph
        self.subgoal = subgoal
        self.arg = []
        self.add_arg(arg, subgoal)

    def _addEntity(self, ent):
        assert isinstance(
            ent,
            Entity), f'non entity {ent} tried to be added to pred {self.name}'
        self.arg.append(ent)
        ent.addPred(self)
        return

    def _addEvent(self, evt):
        assert isinstance(
            evt,
            Event), f'non event {evt} tried to be added to pred {self.name}'
        self.arg.append(evt)
        evt.addPred(self)
        return

    def add_arg(self, args, subgoal):
        assert isinstance(args, list)

        for arg in args:
            assert isinstance(arg, str)

            matched = not arg.startswith('?')
            if not matched:
                arg = arg.lstrip('?').replace('z', 'x')

            t, i = parse(arg)

            if t == 'e':

                if subgoal and matched:
                    matched_e = self.graph.events[i]
                    i += 1000
                elif subgoal and not matched:
                    i += 1000
                else:
                    pass

                if i not in self.graph.events:
                    self.graph.addEvent(Event(i, subgoal))
                event = self.graph.events[i]
                self._addEvent(event)

                if subgoal and matched:
                    event.add_match(matched_e)

            elif t == 'x':

                if subgoal and matched:
                    if i == 200:
                        breakpoint()

                    matched_e = self.graph.entities[i]
                    i += 1000
                elif subgoal and not matched:
                    i += 1000
                else:
                    pass

                if i not in self.graph.entities:
                    self.graph.addEntity(Entity(i, subgoal))
                entity = self.graph.entities[i]
                self._addEntity(entity)

                if subgoal and matched:
                    entity.add_match(matched_e)

            else:
                raise ValueError(f't={t} which should be x or e')

        # Make first arg Event always for preposition
        if len(arg) == 2 and isinstance(args[0], Entity):
            args[0], args[1] = args[1], args[0]
        return


class Entity:
    def __init__(self, i, subgoal=False):
        self.i = int(i)
        self.predicates = []
        self.name = f'x{self.i}'
        self.subgoal = subgoal
        self.matched = None
        self.matched_by = None
        return

    def addPred(self, p):
        assert isinstance(p, Predicate)
        self.predicates.append(p)
        return

    def pos_order(self, pred):
        if pred.pos.startswith('NN'):
            return 200 + pred.i
        elif pred.pos.startswith('JJ'):
            return 100 + pred.i
        elif pred.pos.startswith('CD'):
            return -100 + pred.i
        elif pred.pos.startswith('RB'):
            return 300 + pred.i
        else:
            return -200 + pred.i

    def get_pred_str(self, add_det=False):
        acc = []
        for p in sorted(self.predicates, key=self.pos_order):
            if len(p.arg) == 1:
                acc.append(p)

        # Only prop case
        if len(acc) == 0:
            return self.matched.get_pred_str()

        result = ' '.join([p.name for p in acc])

        if add_det and acc[-1].pos.startswith('NN'):
            result = f'a {result}'

        return result

    def get_prop_str(self):
        acc = []
        for p in sorted(self.predicates, key=self.pos_order):
            if len(p.arg) == 2:
                prop = p.arg[0].get_prop_str()
                acc.append(prop)
        return ' '.join(acc)

    def add_match(self, e):
        self.matched = e
        e.matched_by = self
        return


class Event:
    def __init__(self, i, subgoal=False):
        self.i = int(i)
        self.predicates = []
        self.name = f'e{self.i}'
        self.subgoal = subgoal
        self.matched = None
        self.matched_by = None
        return

    def pos_order(self, pred):
        if pred.pos.startswith('V'):
            return 100 + pred.i
        elif pred.pos.startswith('RB'):
            return 200 + pred.i
        else:
            return 300 + pred.i

    def addPred(self, p):
        assert isinstance(p, Predicate)
        self.predicates.append(p)
        return

    def addRelation(self, x: Entity, name: str):
        assert isinstance(x, Entity) and not hasattr(self, name)
        setattr(self, name.lower(), x)

    def get_pred_str(self, prog=False):
        acc = []
        for p in sorted(self.predicates, key=self.pos_order):
            if len(p.arg) == 1:
                acc.append(p)

        if len(acc) == 0:
            return self.matched.get_pred_str(prog=prog)

        else:

            if prog and acc[0].pos.startswith('VB'):
                acc[0] = progressive(acc[0])

            verb = " ".join([p.name for p in acc])
            if hasattr(self, 'acc'):
                acc = self.acc.get_pred_str()
                verb += f' a {acc}'
            if hasattr(self, 'dat'):
                dat = self.dat.get_pred_str()
                verb += f' to a {dat}'
        return verb

    def get_prop_str(self):
        acc = []
        for p in self.predicates:
            if len(p.arg) == 2:
                x = p.arg[1].get_pred_str()
                acc.append(f'{p.name} a {x}')
        return ' '.join(acc)

    def add_match(self, e):
        self.matched = e
        e.matched_by = self
        return


def parse(x):
    assert isinstance(x, str)
    t = x[0]
    i = x[1:]
    if i == '':
        i = 9999
    else:
        i = int(i)
    return t, i


def progressive(p):
    # TODO change this to spacy or nltk or something
    if p.name.endswith('ing'):
        return
    if p.name.endswith('t'):
        p.name = p.name + 't'
    elif p.name.endswith('e'):
        p.name = p.name.rstrip('e')
    p.name = p.name + 'ing'
    return p
