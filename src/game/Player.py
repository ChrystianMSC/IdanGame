class Player:

    def __init__(self, name):
        self._name = name
        self._is_my_turn = False

    @property
    def name(self):
        return self._name

    @property
    def is_my_turn(self):
        return self._is_running_turn

    def set_turn(self, state):
        self._is_my_turn = state