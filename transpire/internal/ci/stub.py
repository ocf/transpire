import os

from transpire.internal.config import GitModuleConfig


def main():
    # 1. Pull down the remote git repository.
    # 2. Call the `ci()` method, if it exists. Otherwise return success.
    # 3. Run the workflow that the ci() method outputs.

    # TODO: Dependencies?????

    config = GitModuleConfig(
        git=os.environ["GIT_URL"],
        branch=os.environ["GIT_BRANCH"],
        dir=os.environ["DIR"],
    )

    module = config.load_module("transpire_module")
    module.workflow().create()


if __name__ == "__main__":
    main()
