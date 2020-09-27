class Graph:
    def __init__(self):
        self.entities = dict()
        self.events = dict()
        self.predicate = dict()

    def addPred(self, name, args):
        if name in self.predicate:
            name = f'{name}_2'  # fix this
        pred = Predicate(name, args, self)
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

    def get_e(self, e):
        if e.split(' ')[0].lower() in {'subj', 'acc', 'dat'}:
            sr, e_ = e.split(' ')
            t, i = parse(e_)
            assert t == 'e' and hasattr(e_, sr)
            return getattr(self.events[i], sr)
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
        self.args = []
        self.graph = graph
        self.add_arg(arg)

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

    def add_arg(self, args):
        if not isinstance(args, list):
            args = [args]
        for arg in args:
            t, i = parse(arg)
            if t == 'e':
                if i not in self.graph.events:
                    self.graph.addEvent(Event(i))
                self.addEvent(self.graph.events[i])
            elif t == 'x':
                if i not in self.graph.entities:
                    self.graph.addEntity(Entity(i))
                self.addEntity(self.graph.entities[i])
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
        assert isinstance(p, Predicate)
        self.predicates.append(p)
        return

    def get_pred_str(self):
        return ' & '.join([f'{p.name} {self.name}' for p in self.predicates])

    def __repr__(self):
        return self.get_pred_str()


class Event:
    def __init__(self, i):
        self.i = int(i)
        self.predicates = []
        self.name = f'e{self.i}'
        return

    def addPred(self, p):
        assert isinstance(p, Predicate)
        self.predicates.append(p)
        return

    def addRelation(self, x: Entity, name: str):
        assert isinstance(x, Entity) and not hasattr(self, name)
        setattr(self, name.lower(), x)

    def __repr__(self):
        return self.get_pred_str()

    def get_pred_str(self):
        return f'Subj({self.name}) = {self.subj.name} & {self.subj.get_pred_str()}'


def parse(x):
    assert isinstance(x, str)
    return x[0], int(x[1:])
