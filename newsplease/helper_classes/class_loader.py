import importlib


class ClassLoader:
	@classmethod
	def from_string(cls, class_name):
		if "." not in class_name:
			raise ImportError("{0} doesn't look like a module path".format(class_name))

		module_name = ".".join(class_name.split(".")[:-1])
		class_name = class_name.split(".")[-1]

		try:
			loaded_module = importlib.import_module(module_name)
			loaded_class = getattr(loaded_module, class_name)
		except AttributeError and ModuleNotFoundError as e:
			raise ImportError("Module {0} does not exist or does not define a class named {1}".format(module_name,
			                                                                                          class_name)) from e

		return loaded_class
