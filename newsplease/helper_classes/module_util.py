import importlib


class ClassLoader:
	@classmethod
	def from_string(cls, class_name):
		if "." not in class_name:
			raise ImportError(f"{class_name} does't look like a module path")

		module_name = ".".join(class_name.split(".")[:-1])
		class_name = class_name.split(".")[-1]

		try:
			loaded_module = importlib.import_module(module_name)
			loaded_class = getattr(loaded_module, class_name)
		except Exception as e:
			raise ImportError(
				f"Module {module_name} does not exist or does not define a class named {class_name}") from e

		return loaded_class
