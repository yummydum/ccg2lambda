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

    def addRelation(self, event, entity, name, subgoal):

        matched = not entity.startswith('?')
        if not matched:
            entity = entity.lstrip('?')

        t_e, i_e = parse(event)
        t_x, i_x = parse(entity)

        if subgoal:
            if matched:
                i_x += 1000
            else:
                i_x += 500

        event = self.events[i_e]
        entity = self.entities[i_x]
        self.events[event.i].addRelation(entity, name)

        # If the event is matched, add relation of subgoal entity as well (they share relation)
        if subgoal and matched:
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
            for pred in e.predicates:
                subgoal = pred.name
                if pred.pos.startswith('NN'):
                    subgoal = f'a {subgoal}'
                elif pred.pos.startswith('JJ'):
                    pass
                else:
                    continue
                axiom = f'The {e.matched.core_pred.name} is {subgoal}'
                result.append(axiom)
        return result

    def from_matched_events(self):
        result = []
        e_list = [e for e in self.events.values() if e.subgoal and e.matched]
        for e in e_list:
            subject = e.matched.subj.core_pred.name
            # verb advb subgoal
            for pred in e.predicates:
                if pred.pos.startswith('V'):
                    verb = progressive(pred).name
                    axiom = f'The {subject} is {e.add_sr(verb)}'
                    result.append(axiom)
                elif pred.pos.startswith('RB'):
                    axiom = f'The {subject} is doing something {pred.name}'
                    result.append(axiom)

            for prop in e.get_props():
                for arg in prop.arg:
                    if arg != e:
                        break

                # Use the matched entity for prop arg
                if arg.matched is not None:
                    axiom = f'The {subject} is {prop.name} a {arg.matched.core_pred.name}'

                # Use core pred itself if unmatched (these are unmatched subgoal via propositon)
                else:
                    axiom = f'The {subject} is {prop.name} {arg.get_all_pred_str()}'
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

                if subgoal:
                    # If it has corresponding entity then make a new e with + 1000
                    if matched:
                        matched_e = self.graph.events[i]
                        i += 1000
                    # If not matched make a unmatched with +500
                    else:
                        i += 500

                if i not in self.graph.events:
                    self.graph.addEvent(Event(i, subgoal))
                event = self.graph.events[i]
                self._addEvent(event)

                if subgoal and matched:
                    event.add_match(matched_e)

            elif t == 'x':

                if subgoal:
                    # If it has corresponding entity then make a new e with + 1000
                    if matched:
                        matched_e = self.graph.entities[i]
                        i += 1000
                    # If not matched make a unmatched with +500
                    else:
                        i += 500

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
        self.matched = None  # for subgoal entity, this is the matched entity
        self.matched_by = None  # for matched entity, this is the subgoal entity
        self.core_pred = None
        self.core_prop = None
        return

    def addPred(self, p):
        assert isinstance(p, Predicate)
        self.predicates.append(p)

        if p.pos.startswith('NN'):
            self.core_pred = p
        if len(p.arg) == 2:
            self.core_prop = p
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

    def get_all_pred_str(self):
        acc = []
        for p in sorted(self.predicates, key=self.pos_order):
            if len(p.arg) == 1:
                acc.append(p)
        result = ' '.join([p.name for p in acc])
        if acc[-1].pos.startswith('NN'):
            result = f'a {result}'
        return result

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
        self.core_pred = None
        return

    def pos_order(self, pred):
        if pred.pos.startswith('V'):
            return 100 + pred.i
        elif pred.pos.startswith('RB'):
            return 200 + pred.i
        else:
            return 300 + pred.i

    def get_props(self):
        return [x for x in self.predicates if len(x.arg) == 2]

    def addPred(self, p):
        assert isinstance(p, Predicate)
        self.predicates.append(p)
        if p.pos.startswith('V'):
            self.core_pred = p
        return

    def addRelation(self, x: Entity, name: str):
        assert isinstance(x, Entity) and not hasattr(self, name)
        setattr(self, name.lower(), x)

    def add_sr(self, verb):
        if hasattr(self, 'acc'):
            acc = self.acc.core_pred.name
            verb += f' a {acc}'
        elif hasattr(self.matched, 'acc'):
            if self.matched.acc.matched_by is not None:
                acc = self.matched.acc.matched_by.core_pred.name
            else:
                acc = self.matched.acc.core_pred.name
            verb += f' a {acc}'

        if hasattr(self, 'dat'):
            dat = self.dat.core_pred
            verb += f' to a {dat}'
        elif hasattr(self.matched, 'dat'):
            if self.matched.dat.matched_by is not None:
                dat = self.matched.dat.matched_by.core_pred.name
            else:
                dat = self.matched.dat.core_pred.name
            verb += f' to a {dat}'
        return verb

    def get_all_pred_str(self):
        acc = []
        for p in sorted(self.predicates, key=self.pos_order):
            if len(p.arg) == 1:
                acc.append(p)
        result = ' '.join([p.name for p in acc])
        if acc[-1].pos.startswith('NN'):
            result = f'a {result}'
        return result

    def add_match(self, e):
        self.matched = e
        e.matched_by = self
        return


def parse(x):
    assert isinstance(x, str)
    t = x[0]
    i = x[1:]
    if i == '':
        i = 999
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
