def execute_omex(archive_id, debug=True):
    """
    Execute omex.
    """
    # TODO: error handling for cleanup
    matplotlib.pyplot.switch_backend("Agg")

    print("*** START RUNNING OMEX ***")
    results = {}

    # read archive
    archive = get_object_or_404(Archive, pk=archive_id)
    omex_path = str(archive.file.path)

    # execute archive
    # FIXME: execute without making images for speedup
    tmp_dir = tempfile.mkdtemp()
    dgs_all = te.executeOMEX(omex_path, workingDir=tmp_dir)
    if debug:
        print("dgs_all:", dgs_all)