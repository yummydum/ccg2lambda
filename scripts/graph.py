from graphviz import Digraph


class Graph:
    def __init__(self):
        self.entities = dict()
        self.events = dict()
        self.predicate = dict()
        self.relation_subgoal = []
        self.checked_subgoals = []

    def addPred(self, i, name, pos, arg, surf, subgoal):
        if name in self.predicate:
            name = f'{name}_2'  # fix this
        pred = Predicate(i, name, pos, arg, subgoal, surf, self)
        self.predicate[pred.name] = pred
        return

    def addRelation(self, event, entity, name):

        t_e, i_e = parse(event)
        t_x, i_x = parse(entity)

        event = self.events[i_e]
        entity = self.entities[i_x]
        self.events[event.i].addRelation(entity, name)

        # Assuming event and matched event share same predicate argument, copy the argument relation to the subgoal specific event
        if event.matched_by is not None:
            self.events[event.matched_by.i].addRelation(entity, name)
        return

    def addSubgoalRelation(self, event, entity, name):
        if event.startswith('?'):
            event = event.lstrip('?')
            e_matched = False
        else:
            e_matched = True

        if entity.startswith('?'):
            entity = entity.lstrip('?')
            x_matched = False
        else:
            x_matched = True

        t_e, i_e = parse(event)
        t_x, i_x = parse(entity)

        assert t_e == 'e'
        assert t_x == 'x'

        if x_matched:
            i_x += 1000
        else:
            i_x += 500
        if e_matched:
            i_e += 1000
        else:
            i_e += 500

        if i_x not in self.entities:
            matched_x = self.entities[i_x - 1000]
            self.addEntity(Entity(i_x, subgoal=True))
            self.entities[i_x].add_match(matched_x)

        if i_e not in self.events:
            matched_e = self.events[i_e - 1000]
            self.addEvent(Event(i_e, subgoal=True))
            self.entities[i_e].add_match(matched_e)

        event = self.events[i_e]
        entity = self.entities[i_x]
        self.events[event.i].addRelation(entity, name)
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
        # result += self.from_unmatched_entities()  # assume this is handled by matched event (unmatched entity comes from new prop and new pred arg)
        result += self.from_unmatched_events()
        result += self.from_pr_subgoal()
        return result

    def from_matched_entities(self):
        result = []
        e_list = [e for e in self.entities.values() if e.subgoal and e.matched]
        for e in e_list:
            for pred in e.predicates:

                subj = e.matched.core_pred
                subgoal = pred.surf

                if pred.pos == 'IN':
                    continue

                if subj.pos in {'NN', 'NNP'}:
                    copula = 'is'
                else:
                    copula = 'are'

                if pred.pos in {'NN', 'NNP'}:
                    det = f' a '
                else:
                    det = ' '

                axiom = f'The {e.matched.core_pred.surf} {copula}{det}{subgoal}'
                result.append(axiom)
                self.checked_subgoals.append(pred.surf)
        return result

    def from_unmatched_entities(self):
        result = []
        e_list = [
            e for e in self.entities.values() if e.subgoal and not e.matched
        ]
        if len(e_list) > 0:
            breakpoint()
        return result

    def from_matched_events(self):
        result = []
        e_list = [e for e in self.events.values() if e.subgoal and e.matched]
        for e in e_list:
            subject = e.matched.subj.core_pred

            if subject.pos in {'NNS', 'NNPS'}:
                copula = 'are'
            else:
                copula = 'is'

            # verb advb subgoal
            for pred in e.predicates:

                if pred.pos.startswith('V'):
                    verb = progressive(pred).name
                    axiom = f'The {subject.surf} {copula} {e.get_pr(verb)}'
                elif pred.pos.startswith('RB'):
                    verb = progressive(e.core_pred)
                    axiom = f'The {subject.surf} {copula} {e.get_pr(verb)} {pred.surf}'

                elif pred.pos in {'NN', 'NNS'}:
                    axiom = f'The {subject.surf} {copula} a {pred.surf}'
                elif pred.pos == {'NNP', 'NNPS'}:
                    axiom = f'The {subject.surf} {copula} {pred.surf}'

                else:
                    continue

                result.append(axiom)
                self.checked_subgoals.append(pred.name)

            for prop in e.get_props():
                for arg in prop.arg:
                    if arg != e:
                        break

                # Use the matched entity for prop arg
                if arg.matched is not None:
                    axiom = f'The {subject.surf} {copula} {prop.surf} a {arg.matched.core_pred.surf}'
                # Use core pred itself if unmatched (these are unmatched subgoal via propositon)
                else:
                    axiom = f'The {subject.surf} {copula} {prop.surf} {arg.get_all_pred_str()}'
                result.append(axiom)
                self.checked_subgoals.append(prop.surf)
        return result

    def from_unmatched_events(self):

        result = []
        e_list = [
            e for e in self.events.values() if e.subgoal and not e.matched
        ]
        for e in e_list:

            # e? introduced by prop
            if not hasattr(e, 'subj'):
                continue
            # subj is unmatched (completely different sentence?)
            elif e.subj.matched is None:
                continue

            subject = e.subj.matched.core_pred
            if subject.pos in {'NN', 'NNP'}:
                copula = 'is'
            elif subject.pos in {'NNS', 'NNPS'}:
                copula = 'are'
            else:
                copula = 'is'

            # verb advb subgoal
            for pred in e.predicates:
                if pred.pos.startswith('V'):
                    verb = progressive(pred).name
                    axiom = f'The {subject.surf} {copula} {e.get_pr(verb)}'
                elif pred.pos.startswith('RB'):
                    axiom = f'The {subject.surf} {copula} {e.get_pr(verb)} {pred.surf}'
                else:
                    continue

                result.append(axiom)
                self.checked_subgoals.append(pred.name)

            for prop in e.get_props():
                for arg in prop.arg:
                    if arg != e:
                        break

                # Use the matched entity for prop arg
                if arg.matched is not None:
                    axiom = f'The {subject.surf} {copula} {prop.surf} a {arg.matched.core_pred.surf}'

                # Use core pred itself if unmatched (these are unmatched subgoal via propositon)
                else:
                    axiom = f'The {subject.surf} {copula} {prop.surf} {arg.get_all_pred_str()}'
                result.append(axiom)
                self.checked_subgoals.append(prop.name)
        return result

    def from_pr_subgoal(self):
        result = []
        for goal in self.relation_subgoal:
            first, second = goal
            rel, name = first[0], first[1]
            node1 = self.parseRel(name)
            rel2, name2 = second[0], second[1]
            node2 = self.parseRel(name2)

            rel = rel.lower()
            rel2 = rel2.lower()

            if node1.subj.subgoal:
                subj = node1.subj.matched.core_pred
            else:
                subj = node1.subj.core_pred

            verb = node1.core_pred
            target = getattr(node2, rel2).core_pred
            if subj.pos in {'NN', 'NNP'}:
                copula = 'is'
            else:
                copula = 'are'

            if target.pos in {'NN', 'NNP'}:
                det = ' a '
            else:
                det = ' '

            axiom = f'The {subj.surf} {copula} {progressive(verb).name}{det}{target.surf}'
            result.append(axiom)
            self.checked_subgoals.append(goal)
        return result

    def parseRel(self, name):
        unmatched = name.startswith('?')
        if unmatched:
            name = name.lstrip('?')
        t, i = parse(name)

        if unmatched:
            i += 500
        if t == 'x':
            return self.entities[i]
        else:
            return self.events[i]

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
    def __init__(self, i, name, pos, arg, subgoal, surf, graph):
        self.i = i
        self.name = name
        self.surf = surf.lower().split('_')[0]
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

    def get_pr(self, verb):
        """
        Get predicate arguments from subgoal event
        """

        assert self.subgoal

        # check if this event has predicate argument (this should be conclusion specific predicate argument)
        if hasattr(self, 'acc'):
            if self.acc.subgoal:
                if self.acc.matched is not None:
                    acc = self.acc.matched.core_pred
                # unmatched acc which only exists in conclusion
                else:
                    acc = self.acc.core_pred
            else:
                if self.acc.matched_by is not None:
                    acc = self.acc.matched_by.core_pred
                else:
                    acc = self.acc.core_pred

            if acc.pos in {'NN', 'NNP'}:
                verb += f' a {acc.surf}'
            else:
                verb += f' {acc.surf}'

        # if not check matched event in premise
        # self doesn't have acc but matched has? when does this occur
        elif hasattr(self.matched, 'acc'):
            breakpoint()
            if self.matched.acc.matched_by is not None:
                acc = self.matched.acc.matched_by.core_pred
            else:
                acc = self.matched.acc.core_pred

            if acc.pos in {'NN', 'NNP'}:
                verb += f' a {acc.surf}'
            else:
                verb += f' {acc.surf}'

        if hasattr(self, 'dat'):
            if self.dat.subgoal:

                if self.dat.matched is not None:
                    dat = self.dat.matched.core_pred

                # unmatched dat which only exists in conclusion
                else:
                    dat = self.dat.core_pred
            else:
                if self.dat.matched_by is not None and self.dat.matched_by.core_pred is not None:
                    dat = self.dat.matched_by.core_pred
                else:
                    dat = self.dat.core_pred
            if dat.pos in {'NN', 'NNP'}:
                verb += f' to a {dat.surf}'
            else:
                verb += f' to {dat.surf}'

        # if not check matched event in premise
        # self doesn't have dat but matched has? when does this occur
        elif hasattr(self.matched, 'dat'):
            breakpoint()
            if self.matched.dat.matched_by is not None:
                dat = self.matched.dat.matched_by.core_pred
            else:
                dat = self.matched.dat.core_pred

            if dat.pos in {'NN', 'NNP'}:
                verb += f' to a {dat.surf}'
            else:
                verb += f' to {dat.surf}'

        return verb

    def get_all_pred_str(self):
        acc = []
        for p in sorted(self.predicates, key=self.pos_order):
            if len(p.arg) == 1:
                acc.append(p)
        result = ' '.join([p.name for p in acc])
        if acc[-1].pos in {'NN', 'NNP'}:
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
    p.name = p.name.split('_')[0]
    if p.name.endswith('ing'):
        return p
    if p.name.endswith('t'):
        p.name = p.name + 't'
    elif p.name.endswith('e'):
        p.name = p.name.rstrip('e')
    p.name = p.name + 'ing'
    return p
