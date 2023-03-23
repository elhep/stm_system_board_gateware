{
  description = "STM System board controller HDL project";
  
  inputs = {
    nixpkgs.url = github:NixOS/nixpkgs/nixos-21.11;
    src-migen = { url = github:m-labs/migen; flake = false; };
    src-misoc = { type = "git"; url = "https://github.com/m-labs/misoc.git"; submodules = true; flake = false; };
  };

  outputs = { self, nixpkgs, src-migen, src-misoc }: 
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      
      migen = pkgs.python3Packages.buildPythonPackage rec {
        name = "migen";
        src = src-migen;
        propagatedBuildInputs = [ pkgs.python3Packages.colorama ];
      };
      
      asyncserial = pkgs.python3Packages.buildPythonPackage rec {
        pname = "asyncserial";
        version = "0.1";
        src = pkgs.fetchFromGitHub {
          owner = "m-labs";
          repo = "asyncserial";
          rev = "d95bc1d6c791b0e9785935d2f62f628eb5cdf98d";
          sha256 = "0yzkka9jk3612v8gx748x6ziwykq5lr7zmr9wzkcls0v2yilqx9k";
        };
        propagatedBuildInputs = [ pkgs.python3Packages.pyserial ];
      };
      
      misoc = pkgs.python3Packages.buildPythonPackage {
        name = "misoc";
        src = src-misoc;
        doCheck = false;
        propagatedBuildInputs = with pkgs.python3Packages; [ jinja2 numpy migen pyserial asyncserial ];
      };

      stm_sys_board-hdl = pkgs.stdenv.mkDerivation {
        name = "stm_sys_board-hdl";
        phases = [ "buildPhase" "installPhase" ];
        src = self;
        buildInputs = [
         (pkgs.python3.withPackages(f: [ migen misoc litex ]))
          pkgs.yosys
          pkgs.nextpnr
          pkgs.trellis
        ];
        buildPhase = ''
        python $src/stm_sys_board_hdl.py
        '';

        installPhase = ''
        mkdir -p $out
        mv ./build/stm_sys_board.bit $out/stm_sys_board.bit
        mv ./build/stm_sys_board.svf $out/stm_sys_board.svf
        '';

      };

      litex = pkgs.python3Packages.buildPythonPackage {
        pname = "litex";
        version = "2021.12";
        src = pkgs.fetchFromGitHub {
          owner = "enjoy-digital";
          repo = "litex";
          rev = "3fde2512160c78508f02647a507586aa1f5af4e2";
          sha256 = "06jmq4a193fffysdznhnjpa500w38a18xl2i4nw27gzzfdm4frck";
        };
        propagatedBuildInputs = with pkgs.python3Packages; [ migen pyserial requests pythondata-software-compiler_rt ];
        doCheck = false;
      };

      pythondata-software-compiler_rt = pkgs.python3Packages.buildPythonPackage {
        pname = "pythondata-software-compiler_rt";
        version = "2020.11";
        src = pkgs.fetchFromGitHub {
          owner = "litex-hub";
          repo = "pythondata-software-compiler_rt";
          rev = "fcb03245613ccf3079cc833a701f13d0beaae09d";
          sha256 = "06pz4zs8wizx1yp5sv07l9gs71brlr4c8jrxszp0jq7h2g35zyxk";
        };
        doCheck = false;
      };

    openocd-ecp5 = pkgs.openocd.overrideAttrs(oa: {
          version = "unstable-2021-09-15";
          src = pkgs.fetchFromGitHub {
            owner = "openocd-org";
            repo = "openocd";
            rev = "a0bd3c9924870c3b8f428648410181040dabc33c";
            sha256 = "sha256-YgUsl4/FohfsOncM4uiz/3c6g2ZN4oZ0y5vV/2Skwqg=";
            fetchSubmodules = true;
          };
          patches = [ ./openocd-jtagspi-ecp5.patch ];
          nativeBuildInputs = oa.nativeBuildInputs or [] ++ [ pkgs.autoreconfHook269 ];
        });
      
    in {
      devShell.x86_64-linux = pkgs.mkShell {
        name = "stm_sys_board-hdl-dev-shell";
        buildInputs = [
         (pkgs.python3.withPackages(f: [ migen misoc litex ]))
          pkgs.yosys
          pkgs.nextpnr
          pkgs.trellis
          openocd-ecp5
        ];
      };
      
      defaultPackage.x86_64-linux = stm_sys_board-hdl;
    };
      
  
}
