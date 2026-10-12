def main(argv=None):
    """Select a mode before importing its renderer/world dependencies."""
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--mode', choices=('explore', 'editor', 'dialog'), default='explore')
    args, rest = parser.parse_known_args(argv)
    if args.mode == 'dialog':
        from .dialog.dialog import main as run
    elif args.mode == 'editor':
        from .editor.editor import main as run
    else:
        from .explorer.explorer import main as run
    return run(rest)

if __name__ == '__main__':
    main()
