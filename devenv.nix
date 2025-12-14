{ pkgs, lib, config, inputs, ... }:

{
  
  packages = with pkgs; [
    git
  ];

  languages.python = {
    enable = true;
    version = "3.11";
    uv.enable = true;
    uv.sync.enable = true;
  };

  # See full reference at https://devenv.sh/reference/options/
}
