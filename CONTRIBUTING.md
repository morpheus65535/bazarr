# How to Contribute

## Tools required

- Python 3.7.x to 3.11.x (3.9.x is highly recommended and 3.12 or greater is proscribed).
- Pycharm or Visual Studio code IDE are recommended but if you're happy with VIM, enjoy it!
- Git.
- UI testing must be done using Chrome latest version.

## Warning

As we're using Git in the development process, you better disable automatic update of Bazarr in UI or you may get your changes overwritten. Alternatively, you can completely disable the update module by running Bazarr with `--no-update` command line argument.

## Branching

### Basic rules

- `master` contains only stable releases (which have been merged to `master`) and is intended for end-users.
- `development` is the target for testing (around 10% of users) and is not intended for end-users looking for stability.
- `feature` is a temporary feature branch based on `development`.

### Conditions

- `master` is not merged back to `development`.
- `development` is not re-based on `master`.
- all `feature` branches are branched from `development` only.
- Bugfixes created specifically for a feature branch are done there (because they are specific, they're not cherry-picked to `development`).
- We will not release a patch (1.0.x) if a newer minor (1.x.0) has already been released. We only go forward.

## Typical contribution workflow

### Community devs

- Fork the repository or pull the latest changes if you already have forked it.
- Checkout `development` branch.
- Make the desired changes.
- Submit a PR to Bazarr `development` branch.
- Once reviewed, your PR will be merged using Squash and Merge with a meaningful commit message matching our standards.

### Official devs team

- All commits must have a meaningful commit message (ex.: Fixed issue with this, Improved process abc, Added input field to UI, etc.).
- Fixes can be made directly to `development` branch but keep in mind that a pre-release with a beta versioning will be created every day a new push is made.
- Features must be developed in dedicated feature branch and merged back to `development` branch using PR.
- Once reviewed, your PR will be merged using Squash and Merge with a meaningful message.
