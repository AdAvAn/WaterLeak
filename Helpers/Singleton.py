class Singleton(object):
   
    _instances = {}

    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            instance = super(Singleton, class_).__new__(class_)
            class_._instances[class_] = instance
        return class_._instances[class_]
