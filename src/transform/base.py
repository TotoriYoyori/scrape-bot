class TransformStepCollection:
    """Base class for groups of reusable transform steps.

    Subclasses can add new transform steps by creating public ``staticmethod``
    functions. This class also provides simple helper methods to explore the
    available steps and view their documentation.

    Examples:
        >>> SimpleTransform.help()
        >>> SimpleTransform.methods()
        ['drop_columns', 'reset_index']
        >>> SimpleTransform.describe("drop_columns")
    """

    @classmethod
    def _registered_methods(cls) -> dict[str, staticmethod]:
        """Return public static methods registered on the collection.

        Returns:
            A mapping of method names to their ``staticmethod`` descriptors.
        """
        return {
            name: descriptor
            for name, descriptor in cls.__dict__.items()
            if not name.startswith("_") and isinstance(descriptor, staticmethod)
        }

    @classmethod
    def metadata(cls) -> list[dict[str, str]]:
        """Return structured metadata for registered transform methods.

        Returns:
            A list of dictionaries containing each method's name, signature,
            full docstring, and shortened summary.
        """
        records: list[dict[str, str]] = []

        for name, descriptor in cls._registered_methods().items():
            method = descriptor.__func__
            doc = inspect.getdoc(method) or "No docstring available."
            summary = doc.splitlines()[0]
            records.append({
                "name": name,
                "signature": str(inspect.signature(method)),
                "doc": doc,
                "summary": summary if len(summary) <= 88 else f"{summary[:85]}...",
            })

        return records

    @classmethod
    def methods(cls) -> list[str]:
        """Return the names of registered transform methods.

        Returns:
            A list of public static method names available on the collection.
        """
        return [record["name"] for record in cls.metadata()]

    @classmethod
    def help(cls) -> None:
        """Display available transform methods with signatures and summaries in the console.

        This is the first-stop overview for users who do not yet know which
        transform methods are available.
        """
        lines = [f"{cls.__name__} methods:"]

        for record in cls.metadata():
            lines.append(
                f"- {record['name']}{record['signature']}: {record['summary']}"
            )

        print("\n".join(lines))

    @classmethod
    def describe(cls, func_name: str) -> None:
        """Display detailed documentation for one transform method in the console.

        Args:
            func_name: Name of the transform method to describe.
        """
        records = {
            record["name"]: record
            for record in cls.metadata()
        }
        record = records.get(func_name)

        if record is None:
            available_methods = ", ".join(records) or "none"
            print(
                f"No transform method named '{func_name}' found on {cls.__name__}.\n"
                f"Available methods: {available_methods}"
            )
            return

        print(f"{cls.__name__}.{record['name']}{record['signature']}\n\n{record['doc']}")