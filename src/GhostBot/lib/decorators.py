
# noinspection PyPep8Naming
class classproperty(property):
    # noinspection PyMethodOverriding
    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)