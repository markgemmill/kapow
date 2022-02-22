class Handler:
    def __init__(self, name, messages, func=None, raise_err=False):
        self.messages = messages
        self.name = name
        self.raise_err = raise_err
        self.func = func

    def __call__(self, app, ctx):
        self.messages.append(f"{self.name}")
        if self.func:
            self.func(app, ctx, self.messages)
        if self.raise_err:
            raise Exception(f"{self.name} raised an error")
        return app, ctx

    def command(self):
        def _command(app, ctx):
            self.messages.append(f"{self.name} HANDLER")

            def __command(*args):
                self.messages.append(f"{self.name} CALLED")
                if self.raise_err:
                    raise Exception(f"{self.name} raised an error")

            app.command = __command
            return app, ctx

        return _command

    def error_handler(self):
        def __command(appname, ctx, error):
            self.messages.append(f"{self.name} {error}")

        return __command


CLI_DOCS = """test v0.1.0

Usage:
  test run [--debug]
  test --help
  test --version

Options:
  --debug        Run in debug mode.
  -h --help      Show this help message.
  -v --version   Show app version.
"""