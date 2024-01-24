{
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
      in
      with self.packages.${system};
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            poetry
            jq
          ];
        };

        packages = {
          kpconn = pkgs.writeScript "kpconn-runner" ''
            ${kpconn-deps}/bin/flask --app kpconn/server run -p 3000
          '';


          kpconn-deps = (mkPoetryApplication {
            projectDir = ./.;
            python = pkgs.python311;
          }).dependencyEnv;
        };
      }
    );
}
          # kpconn = pkgs.stdenv.mkDerivation {
          #   name = "openera-api-server";
          #   src = pkgs.nix-gitignore.gitignoreSourcePure [
          #     ''
          #       *
          #     ''
          #   ] ./.;
          #   nativeBuildInputs = [
          #     pkgs.makeWrapper
          #   ];
          #   installPhase = ''
          #     mkdir -p $out/bin $out/etc
          #     cp run.sh $out/bin/openera
          #     cp -r sdf-config $out/etc
          #   '';
          #   # Make the Python dependencies available to to the run script.
          #   postFixup = ''
          #     wrapProgram $out/bin/openera \
          #       --prefix PATH : ${pkgs.lib.makeBinPath [
          #         api-server-deps
          #       ]}
          #   '';
          # };
