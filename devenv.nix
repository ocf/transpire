{ pkgs, lib, config, inputs, ... }:

{
  
  env.PYTHONPATH = "${config.devenv.root}";

  packages = with pkgs; [
    git
  ];

  languages.python = {
    enable = true;
    version = "3.11";
      venv = {
      enable = true;
      requirements = ''
        PyYAML==6.0
        kubernetes==25.3.0
        click==8.1.3
        loguru==0.7.2
        pydantic==2.7.0
        hvac==1.0.2
        requests==2.28.2
        tomlkit==0.12.4

        # dev dependencies
        mypy==1.2.0
        black==22.12.0
        types-PyYAML==6.0.4
        types-requests==2.28.2
        flake8==6.0.0
        isort==5.11.4
        pre-commit==4.1.0
        pytest==7.2.1
        coverage[toml]==6.3.2

        # kubernetes-typed from GitHub tag
        git+https://github.com/nikhiljha/kubernetes-typed.git@v25.3.0
      '';
      };
  };

  # See full reference at https://devenv.sh/reference/options/
}
