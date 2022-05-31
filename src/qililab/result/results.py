"""Results class."""
from dataclasses import dataclass, field
from typing import List, Tuple

from qililab.result.qblox_result import QbloxResult
from qililab.result.result import Result
from qililab.utils import Loop


@dataclass
class Results:
    """Results class."""

    @dataclass
    class ExecutionResults:
        """ExecutionResults class."""

        @dataclass
        class SequenceResults:
            """SequenceResults class."""

            results: List[Result] = field(default_factory=list)

            def add(self, result: Result):
                """Add result.

                Args:
                    result (Result): Result object.
                """
                self.results.append(result)

            def probabilities(self) -> List[Tuple[float, float]]:
                """Probabilities of being in the ground and excited state of all the nested Results classes.

                Returns:
                    List[List[Tuple[float, float]]]: Probabilities.
                """
                return [result.probabilities() for result in self.results]

            def acquisitions(self) -> List[Tuple[float, float, float, float]]:
                """QbloxResult acquisitions of all the nested Results classes.

                Returns:
                    List[List[Tuple[float, float, float, float]]]: Acquisition values.
                """
                results = []
                for result in self.results:
                    if not isinstance(result, QbloxResult):
                        raise ValueError(f"{type(result).__name__} class doesn't have an acquisitions method.")
                    results.append(result.acquisitions())
                return results

        results: List[SequenceResults] = field(default_factory=list)

        def new(self):
            """Add new SequenceResults to the results list."""
            self.results.append(self.SequenceResults())

        def add(self, result: Result):
            """Add result object to the last SequenceResults class in the list.

            Args:
                result (Result): Result object.
            """
            self.results[-1].add(result)

        def probabilities(self) -> List[List[Tuple[float, float]]]:
            """Probabilities of being in the ground and excited state of all the nested Results classes.

            Returns:
                List[List[Tuple[float, float]]]: Probabilities.
            """
            return [result.probabilities() for result in self.results]

        def acquisitions(self) -> List[List[Tuple[float, float, float, float]]]:
            """QbloxResult acquisitions of all the nested Results classes.

            Returns:
                List[List[Tuple[float, float, float, float]]]: Acquisition values.
            """
            return [result.acquisitions() for result in self.results]

    loop: Loop
    results: List[ExecutionResults] = field(default_factory=list)

    def add(self, execution_results: ExecutionResults):
        """Append an ExecutionResults object.

        Args:
            execution_results (ExecutionResults): ExecutionResults object.
        """
        self.results.append(execution_results)

    def probabilities(self) -> List[List[List[Tuple[float, float]]]]:
        """Probabilities of being in the ground and excited state of all the nested Results classes.

        Returns:
            List[List[List[Tuple[float, float]]]]: List of probabilities of each executed loop and sequence.
        """
        return [result.probabilities() for result in self.results]

    def acquisitions(self) -> List[List[List[Tuple[float, float, float, float]]]]:
        """QbloxResult acquisitions of all the nested Results classes.

        Returns:
            List[List[Tuple[float, float, float, float]]]: Acquisition values.
        """
        return [result.acquisitions() for result in self.results]
