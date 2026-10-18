import typer

app = typer.Typer(help="Style DNA of Polish rap: fetching, processing, statistics, pages.", no_args_is_help=True)


def _echo_counts(counts: dict) -> None:
    for name, n in counts.items():
        typer.echo(f"{name}: {n}")


# --- corpus ---------------------------------------------------------------------------------------------------------

@app.command()
def info():
    """Show project paths and whether the external resources are in place."""
    from rapdna import paths

    for name in ["PANPHON_SIMILARITY", "PHONETIC_DICT", "HOMONYMS", "SLANG"]:
        p = getattr(paths, name)
        typer.echo(f"{name:18} {'OK     ' if p.exists() else 'MISSING'} {p.relative_to(paths.ROOT)}")


@app.command("prepare-resources")
def prepare_resources():
    """Convert the phonetic dictionary CSV to Parquet."""
    from rapdna import paths
    from rapdna.text.phonetics import build_dictionary_parquet

    n = build_dictionary_parquet(paths.RESOURCES / "plwordnet_phonetic_dict.csv", paths.PHONETIC_DICT)
    typer.echo(f"Saved {n} entries to {paths.PHONETIC_DICT.relative_to(paths.ROOT)}")


@app.command()
def resolve():
    """Fill in the Genius ids of the rappers in config/artists.yaml."""
    from rapdna.genius.api import GeniusAPI
    from rapdna.ingest import resolve_ids

    for name, gid, cands in resolve_ids(GeniusAPI()):
        if gid:
            typer.echo(f"{name}: {gid}")
        else:
            typer.echo(f"{name}: ambiguous, enter one of these by hand: "
                       + ", ".join(f"{c['name']}={c['id']}" for c in cands))


@app.command()
def albums(artist: str):
    """List a rapper's albums on Genius with song counts (to copy into config/artists.yaml)."""
    from rapdna.genius.api import GeniusAPI
    from rapdna.ingest import album_summary, load_config, own_songs

    a = next(x for x in load_config()["artists"] if x["name"].casefold() == artist.casefold())
    for album, n in album_summary(own_songs(GeniusAPI(), a["genius_id"])):
        typer.echo(f"{n:4}  {album}")


@app.command()
def fetch(artist: str = typer.Option(None, help="Only this rapper (default: everyone in the config)")):
    """Download the lyrics of the albums listed in config/artists.yaml to data/songs.jsonl."""
    from rapdna.genius.api import GeniusAPI
    from rapdna.genius.scrape import GeniusScraper
    from rapdna.ingest import fetch_artist, load_config

    api, scraper = GeniusAPI(), GeniusScraper()
    for a in load_config()["artists"]:
        if artist and a["name"].casefold() != artist.casefold():
            continue
        if not a.get("albums"):
            typer.echo(f"{a['name']}: no albums in the config, skipped")
            continue
        typer.echo(a["name"])
        typer.echo(f"  new songs: {fetch_artist(api, scraper, a, log=typer.echo)}")


@app.command()
def process():
    """Lyrics → lines, words with IPA and morphology, rhymes (data/parquet)."""
    from rapdna.pipeline import process as run

    _echo_counts(run(log=typer.echo))


@app.command()
def rhymes(train: bool = typer.Option(False, help="Retrain the Hirjee & Brown baseline")):
    """Rhymes only, without recomputing pronunciation and lemmas."""
    from rapdna.pipeline import detect_rhymes

    _echo_counts(detect_rhymes(train_model=train, log=typer.echo))


# --- statistics -----------------------------------------------------------------------------------------------------

@app.command()
def figures():
    """Stylistic figures per line (data/parquet/figures.parquet) and pun / paronomasia candidates (data/candidates)."""
    import pandas as pd

    from rapdna import paths
    from rapdna.figures import candidates
    from rapdna.figures.compute import FIGURE_COLUMNS, compute
    from rapdna.phonology import soundvec

    w = pd.read_parquet(paths.PARQUET / "words.parquet")
    soundvec.build(dict(zip(w.form.str.lower(), w.ipa)))
    df = compute(log=typer.echo)
    typer.echo(df[FIGURE_COLUMNS].mean().round(3).to_string())
    typer.echo(f"candidates: {candidates.build(log=typer.echo)}")


@app.command()
def stats():
    """Technical statistics per rapper and album, DNA, similarity and the scene map → data/stats/"""
    import json

    import yaml

    from rapdna import paths
    from rapdna.stats.dna import normalize, similarity
    from rapdna.stats.scene import scene
    from rapdna.stats.technical import compute

    out = paths.STATS
    out.mkdir(parents=True, exist_ok=True)
    artists, albums = compute(log=typer.echo)
    defs = yaml.safe_load((paths.CONFIG / "stats.yaml").read_text(encoding="utf-8"))
    keys = [k for k, d in defs.items() if d.get("dna")]
    z, pct = normalize(artists, keys)
    sim = similarity(z)
    (out / "scene_map.json").write_text(json.dumps(scene(albums, defs), ensure_ascii=False, indent=1), encoding="utf-8")
    artists.to_csv(out / "artists.csv", index=False)
    albums.to_csv(out / "albums.csv", index=False)
    z.to_csv(out / "dna_z.csv")
    pct.to_csv(out / "dna_percentile.csv")
    sim.to_csv(out / "similarity.csv")
    (out / "dna.json").write_text(json.dumps({
        "definitions": defs, "artists": artists.to_dict("records"), "albums": albums.to_dict("records"),
        "z": z.to_dict("index"), "percentile": pct.to_dict("index"), "similarity": sim.to_dict("index"),
    }, ensure_ascii=False, default=float), encoding="utf-8")
    typer.echo(f"Saved results to {out.relative_to(paths.ROOT)}")


@app.command()
def themes(refit: bool = typer.Option(False, help="Recompute topics and domain lexicons")):
    """Thematic layer: topics (mmlw + BERTopic), vocabulary domains, perspective, references, Genius annotations."""
    from rapdna.stats import domains, thematic, topics

    typer.echo(f"Genius annotations (new): {thematic.fetch_annotations()}")
    if refit or not (topics.OUT / "topics.json").exists():
        typer.echo(f"topics: {topics.fit(log=typer.echo)}")
    if refit or not (topics.OUT / "domain_lexicons.json").exists():
        lex = domains.lexicons(log=typer.echo)
        typer.echo("domains: " + ", ".join(f"{k} {len(v)}" for k, v in lex.items()))
    typer.echo(thematic.compute(log=typer.echo).round(3).to_string())


@app.command()
def surface():
    """Song structure, producers, vocabulary classes, self-mentions and favourite phrases → data/stats/"""
    from rapdna.stats.surface import run

    _, art, _, _ = run(log=typer.echo)
    typer.echo(art.drop(columns=["main_producers"]).round(2).to_string(index=False))


@app.command()
def textual():
    """Tense and mood, comparisons, rare words, repetitiveness, ad-libs, collaborations → data/stats/"""
    from rapdna.stats.textual import run

    run(log=typer.echo)


@app.command()
def reliability():
    """Rapper-vs-song test for every feature (ICC, eta², songs needed) → data/stats/reliability.csv"""
    from rapdna.stats.reliability import run

    typer.echo(run(log=typer.echo).to_string(index=False))


@app.command()
def profiles():
    """Rapper profiles (distinguishing traits) → data/stats/profiles.json and the page site/dna.html"""
    from rapdna.site.profiles_page import build
    from rapdna.stats.profile import run

    run()
    typer.echo(f"Saved {build()}")


# --- local views (full lyrics: never publish) -----------------------------------------------------------------------

@app.command()
def browser():
    """Local song browser with marked devices → data/rhyme_view/songs.html"""
    from rapdna.site.browser import build

    typer.echo(f"Saved {build(log=typer.echo)}")


@app.command("rhymes-for")
def rhymes_for(word: str, n: int = typer.Option(15, help="How many rhyme tails to show")):
    """What rhymes with a word (rule-based ruler, corpus vocabulary)."""
    from rapdna.rhymes.search import load_index
    from rapdna.text.phonetics import Lexicon

    lex = Lexicon()
    lex.load({word})
    for score, t, words in load_index().rhymes(word, lex[word], k=n):
        typer.echo(f"{score:6.2f}  [{t}]  {', '.join(words)}")


@app.command()
def audio(song_id: int, device: str = typer.Option("cuda", help="cuda or cpu")):
    """Audio pilot for one song: YouTube → vocals → words in time → beats → karaoke page (data/audio/, local only)."""
    import pandas as pd

    from rapdna import paths
    from rapdna.audio import align, fetch as yt, karaoke, signal

    meta = pd.read_parquet(paths.PARQUET / "lines.parquet", columns=["song_id", "artist", "title"])
    artist, title = meta[meta.song_id == song_id].iloc[0][["artist", "title"]]
    raw = yt.download(song_id, artist, title, log=typer.echo)
    if raw is None:
        raise typer.Exit(1)
    vocals = signal.separate_vocals(raw, song_id, device)
    beats, downbeats = signal.beats(raw, device)
    words = align.align(song_id, vocals, device)
    align.save(song_id, words, beats, downbeats)
    typer.echo(f"words: {len(words)}, mean confidence {words.score.mean():.2f}, beats: {len(beats)}, "
               f"bars: {len(downbeats)}")
    typer.echo(f"Saved {karaoke.build(song_id, f'{artist} - {title}')}")


# --- validation -----------------------------------------------------------------------------------------------------

@app.command()
def gold():
    """Gold set for manual labelling (300 rhyme pairs, 500 lines) → data/validation/gold/"""
    from rapdna.validate.gold import GOLD, build

    _echo_counts(build())
    typer.echo(f"Files in {GOLD}")


@app.command()
def calibrate(reference: str = typer.Option(None, help="Whose labels are the reference (default: „ty” if present)")):
    """Precision, recall, kappa of the Hirjee & Brown baseline; writes config/thresholds.yaml and redoes the rhymes."""
    import yaml

    from rapdna.pipeline import detect_rhymes
    from rapdna.validate.score import evaluate

    typer.echo(yaml.safe_dump(evaluate(reference), allow_unicode=True, sort_keys=False))
    _echo_counts(detect_rhymes(train_model=False, log=typer.echo))


@app.command("gold-r")
def gold_r():
    """Gold set of the rule-based ruler: 300 candidates for a blind review → data/validation/gold_r/"""
    from rapdna.validate.gold_r import GOLD_R, build

    typer.echo(f"{build()} candidates in {GOLD_R}")


@app.command("calibrate-r")
def calibrate_r():
    """Thresholds of the rule-based ruler on its gold sets (config/thresholds_r.yaml), then redo the rhymes."""
    import yaml

    from rapdna.pipeline import detect_rhymes
    from rapdna.validate.gold_r import evaluate

    typer.echo(yaml.safe_dump(evaluate(), allow_unicode=True, sort_keys=False))
    _echo_counts(detect_rhymes(train_model=False, log=typer.echo))


@app.command()
def sample(n: int = 50, seed: int = 42):
    """Random sample of detected rhymes for a manual review → data/validation/rymy_<seed>.csv"""
    from rapdna.validate.sample import SAMPLES, rhyme_sample

    SAMPLES.mkdir(parents=True, exist_ok=True)
    out = SAMPLES / f"rymy_{seed}.csv"
    rhyme_sample(n, seed).to_csv(out, index=False, encoding="utf-8-sig", sep=";")
    typer.echo(f"Saved {out}")


@app.command("sample-figures")
def sample_figures(n: int = 30, seed: int = 42):
    """Random alliterations, anaphoras and epiphoras for a manual review → data/validation/figury_<seed>.csv"""
    from rapdna.validate.sample import SAMPLES, figure_sample

    SAMPLES.mkdir(parents=True, exist_ok=True)
    out = SAMPLES / f"figury_{seed}.csv"
    figure_sample(n, seed).to_csv(out, index=False, encoding="utf-8-sig", sep=";")
    typer.echo(f"Saved {out}")


@app.command("compare-rhymes")
def compare_rhymes():
    """Compare the internal-rhyme methods on the reference rhyme annotations (data/rhyme_annotations)."""
    from rapdna.validate import compare_methods

    compare_methods.run()


# --- experiments ----------------------------------------------------------------------------------------------------

@app.command("rhyme-map")
def rhyme_map(n: int = typer.Option(300, help="How many of the most frequent units to show")):
    """Experiment: rhyme units: score matrix of unit pairs (variant A) and a map to look at → data/rhyme_units/"""
    import pandas as pd

    from rapdna import paths
    from rapdna.experiments import unit_map, units
    from rapdna.rhymes.hb import RhymeModel

    w = pd.read_parquet(paths.PARQUET / "words.parquet", columns=["form", "ipa"])
    counts = units.corpus_units(w)
    us, m = units.build_matrix(RhymeModel.load(), counts, log=typer.echo)
    typer.echo(f"Saved {unit_map.write(us, m, counts, units.unit_examples(w), n)}")


@app.command("rhyme-units-b")
def rhyme_units_b():
    """Experiment: variant B of rhyme units (scores learned for unit pairs) against the baseline on the gold set."""
    import pandas as pd
    import yaml

    from rapdna import paths
    from rapdna.experiments import units
    from rapdna.pipeline import training_tails
    from rapdna.rhymes.hb import RhymeModel, make_tail
    from rapdna.text.phonetics import Lexicon
    from rapdna.validate.score import compare, rescore

    base = RhymeModel.load()
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    typer.echo("variant B:")
    b = units.train_units(training_tails(lines, words), base, log=typer.echo)
    report = {"gold_set": compare(rescore({"A": base.score, "B": b.score}), ["A", "B"])}
    lex = Lexicon()
    pairs = [("kasa", "masa", 1), ("tango", "bagno", 1), ("kasa", "kosa", 0), ("bieda", "woda", 0), ("zamek", "zamach", 0)]
    lex.load({w for a, c, _ in pairs for w in (a, c)})
    report["known_pairs"] = [{"pair": f"{a} / {c}", "rhyme": bool(r),
                     **{n: round(m(make_tail([(a, lex[a])]), make_tail([(c, lex[c])])), 2)
                        for n, m in (("A", base.score), ("B", b.score))}}
                    for a, c, r in pairs]
    (units.OUT / "variant_b.yaml").write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    typer.echo(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    app()
