class Graph:
    def __init__(self):
        self.entities = dict()
        self.events = dict()
        self.predicate = dict()

    def addPred(self, name, arg):
        if name in self.predicate:
            name = f'{name}_2'  # fix this
        pred = Predicate(name, arg, self)
        self.predicate[pred.name] = pred
        return

    def addPreposition(self, name, args):
        if name in self.predicate:
            name = f'{name}_2'  # fix this
        pred = Preposition(name, args, self)
        self.predicate[pred.name] = pred
        return

    def addRelation(self, event, entity, name):
        t_e, i_e = parse(event)
        t_x, i_x = parse(entity)
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

    def get_e(self, e: str):
        assert isinstance(e, str)
        if e.split(' ')[0].lower() in {'subj', 'acc', 'dat'}:
            sr, e_ = e.split(' ')
            sr = sr.lower()
            t, i = parse(e_)
            evt = self.get_e(e_)
            assert t == 'e' and hasattr(evt, sr)
            return getattr(evt, sr)
        else:
            t, i = parse(e)
            if t == 'x':
                return self.entities[i]
            elif t == 'e':
                return self.events[i]
            else:
                raise ValueError()


class Predicate():
    def __init__(self, name, arg, graph):
        self.name = name
        self.graph = graph
        self.arg = None
        self.add_arg(arg)

    def _addEntity(self, ent):
        assert isinstance(
            ent,
            Entity), f'non entity {ent} tried to be added to pred {self.name}'
        self.arg = ent
        ent.addPred(self)
        return

    def _addEvent(self, evt):
        assert isinstance(
            evt,
            Event), f'non event {evt} tried to be added to pred {self.name}'
        self.arg = evt
        evt.addPred(self)
        return

    def add_arg(self, arg):
        assert isinstance(arg, str) or (isinstance(arg, list)
                                        and len(arg) == 1)
        if isinstance(arg, list):
            arg = arg[0]

        t, i = parse(arg)
        if t == 'e':
            if i not in self.graph.events:
                self.graph.addEvent(Event(i))
            self._addEvent(self.graph.events[i])
        elif t == 'x':
            if i not in self.graph.entities:
                self.graph.addEntity(Entity(i))
            self._addEntity(self.graph.entities[i])
        else:
            raise ValueError()
        return


class Preposition():
    def __init__(self, name, args, graph):
        self.name = name
        self.graph = graph
        self.entity = None
        self.event = None
        assert isinstance(args, list) and len(args) == 2
        self.add_arg(args)

    def _addEntity(self, ent):
        assert isinstance(
            ent,
            Entity), f'non entity {ent} tried to be added to pred {self.name}'
        self.entity = ent
        ent.addPred(self)
        return

    def _addEvent(self, evt):
        assert isinstance(
            evt,
            Event), f'non event {evt} tried to be added to pred {self.name}'
        self.event = evt
        evt.addPred(self)
        return

    def add_arg(self, args):
        for arg in args:
            t, i = parse(arg)
            if t == 'e':
                if i not in self.graph.events:
                    self.graph.addEvent(Event(i))
                self._addEvent(self.graph.events[i])
            elif t == 'x':
                if i not in self.graph.entities:
                    self.graph.addEntity(Entity(i))
                self._addEntity(self.graph.entities[i])
            else:
                raise ValueError()
        return


class Entity:
    def __init__(self, i):
        self.i = int(i)
        self.predicates = []
        self.name = f'x{self.i}'
        return

    def addPred(self, p):
        assert isinstance(p, Predicate) or isinstance(p, Preposition)
        self.predicates.append(p)
        return

    def get_pred_str(self):
        acc = []
        for p in self.predicates:
            if isinstance(p, Predicate):
                acc.append(f'{p.name} {self.name}')
        return ' & '.join(acc)

    def get_prop_str(self):
        acc = []
        for p in self.predicates:
            if isinstance(p, Preposition):
                prop_str = f'{p.event.get_pred_str()} & {p.event.get_pred_str(subj=False)} & {p.entity.get_pred_str()} & {p.name} {p.entity} {p.event}'
                acc.append(prop_str)
        return ' & '.join(acc)

    def __repr__(self):
        return self.get_pred_str()


class Event:
    def __init__(self, i):
        self.i = int(i)
        self.predicates = []
        self.name = f'e{self.i}'
        return

    def addPred(self, p):
        assert isinstance(p, Predicate) or isinstance(p, Preposition)
        self.predicates.append(p)
        return

    def addRelation(self, x: Entity, name: str):
        assert isinstance(x, Entity) and not hasattr(self, name)
        setattr(self, name.lower(), x)

    def get_pred_str(self, subj=True):
        if subj:
            return f'Subj({self.name}) = {self.subj.name} & {self.subj.get_pred_str()}'
        else:
            acc = []
            for p in self.predicates:
                if isinstance(p, Predicate):
                    acc.append(f'{p.name} {self.name}')
            return ' & '.join(acc)

    def get_prop_str(self):
        acc = []
        for p in self.predicates:
            if isinstance(p, Preposition):
                prop_str = f'{p.event.get_pred_str()} & {p.event.get_pred_str(subj=False)} & {p.entity.get_pred_str()} & {p.name} {p.entity} {p.event}'
                acc.append(prop_str)
        return ' & '.join(acc)

    def __repr__(self):
        return self.get_pred_str(subj=False)


def parse(x):
    assert isinstance(x, str)
    return x[0], int(x[1:])
