import multiprocessing
import time

from rally import consts
from rally.task import runner
from rally.task import utils as butils


def _run_scenario_once_with_sleep(args):
    iteration, cls, method_name, context_obj, kwargs, pause = args

    # Time to take a break
    time.sleep(pause)
    args = (iteration, cls, method_name, context_obj, kwargs)
    return runner._run_scenario_once(args)


@runner.configure(name="constant_for_duration_with_break")
class ConstantForDurationWithPauseScenarioRunner(runner.ScenarioRunner):
    """Extends common constant_for_duration runner with configurable sleep.

    Useful for scenarios whit expected failures for preventing generation
    of large amount of fail results.
    """

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "properties": {
            "type": {
                "type": "string"
            },
            "concurrency": {
                "type": "integer",
                "minimum": 1
            },
            "duration": {
                "type": "number",
                "minimum": 0.0
            },
            "timeout": {
                "type": "number",
                "minimum": 1
            },
            "pause": {
                "type": "number",
                "minimum": 0.01
            }
        },
        "required": ["type", "duration"],
        "additionalProperties": False
    }

    @staticmethod
    def _iter_scenario_args(cls, method, ctx, args, aborted, pause):
        def _scenario_args(i):
            if aborted.is_set():
                raise StopIteration()
            return (i, cls, method,
                    runner._get_scenario_context(ctx), args, pause)
        return _scenario_args

    def _run_scenario(self, cls, method, context, args):
        """Runs the specified benchmark scenario with given arguments.

        :param cls: The Scenario class where the scenario is implemented
        :param method_name: Name of the method that implements the scenario
        :param context: Benchmark context that contains users, admin & other
                        information, that was created before benchmark started.
        :param args: Arguments to call the scenario method with

        :returns: List of results fore each single scenario iteration,
                  where each result is a dictionary
        """
        timeout = self.config.get("timeout", 600)
        concurrency = self.config.get("concurrency", 1)
        duration = self.config.get("duration")
        pause = self.config.get("pause", 0.5)

        pool = multiprocessing.Pool(concurrency)

        run_args = butils.infinite_run_args_generator(
            self._iter_scenario_args(cls, method, context, args,
                                     self.aborted, pause))
        iter_result = pool.imap(_run_scenario_once_with_sleep, run_args)

        start = time.time()
        while True:
            try:
                result = iter_result.next(timeout)
            except multiprocessing.TimeoutError as e:
                result = runner.format_result_on_timeout(e, timeout)
            except StopIteration:
                break

            self._send_result(result)

            if time.time() - start > duration:
                break

        pool.terminate()
        pool.join()
