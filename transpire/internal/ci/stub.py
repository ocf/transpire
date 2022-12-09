import os

from transpire.internal.config import GitModuleConfig


def main():
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
