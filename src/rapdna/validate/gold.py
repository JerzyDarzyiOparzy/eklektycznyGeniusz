"""Gold set for manual labelling (plan: about 300 rhyme pairs and 500 lines).

Rhyme pairs are drawn stratified over the WHOLE range of model scores (pairs the model rejected too), so that the labels
give precision, recall and a threshold. The model score is hidden from the annotator (so it does not suggest the
answer) and kept in a separate key file.

Files go to data/validation/gold/: a CSV for a spreadsheet plus tasks and configurations for Label Studio. The sheets
are for Polish annotators, so their column names and instructions are Polish; `SHEET_FIGURES` maps them to the
figure columns used in the code.
"""
import json

import pandas as pd

from rapdna import paths

GOLD = paths.DATA / "validation" / "gold"
SHEET_FIGURES = {"alliteration": "aliteracja", "anaphora": "anafora", "epiphora": "epifora",
                 "parallelism": "paralelizm", "enjambment": "przerzutnia", "onomatopoeia": "onomatopeja",
                 "phrase_repetition": "powtorzenie_frazy", "assonance_chain": "lancuch_asonansow",
                 "consonance_chain": "lancuch_konsonansow"}
FIGURE_HELP = {
    "aliteracja": "co najmniej 3 bliskie słowa treściowe w wersie zaczynają się tą samą głoską",
    "anafora": "wers zaczyna się tak samo jak poprzedni (nie licz samego „i/a/bo/że”)",
    "epifora": "wers kończy się tym samym słowem co poprzedni (nie licz ech i ad-libów)",
    "paralelizm": "wers ma tę samą budowę składniową co poprzedni („Mam X, mam Y”)",
    "przerzutnia": "zdanie nie kończy się z wersem, tylko przechodzi do następnego",
    "onomatopeja": "w wersie jest wyraz dźwiękonaśladowczy (bum, skrrt, puk puk)",
    "powtorzenie_frazy": "w wersie powtarza się fraza z co najmniej 2 słów",
    "lancuch_asonansow": "co najmniej 3 słowa w wersie mają tę samą akcentowaną samogłoskę i słychać to jako efekt",
    "lancuch_konsonansow": "co najmniej 3 słowa w wersie powtarzają te same spółgłoski (nie tylko na początku)",
}


def _mark(toks: pd.DataFrame, w: int) -> str:
    return " ".join(f"«{f}»" if i == w else f for i, f in zip(toks.w, toks.form))


def rhyme_gold(n_end: int = 200, n_internal: int = 100, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    cands = pd.read_parquet(paths.PARQUET / "candidates.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    by_line = {u: g.sort_values("w") for u, g in words[words.line_uid.isin(set(cands.line_a) | set(cands.line_b))]
               .groupby("line_uid")}
    parts = []
    for kind, n in (("end", n_end), ("internal", n_internal)):
        c = cands[cands.kind == kind].copy()
        c["bin"] = pd.qcut(c.score, 10, labels=False, duplicates="drop")
        per = n // c.bin.nunique()
        parts.append(c.groupby("bin", group_keys=False).sample(per, random_state=seed))
    s = pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    s.insert(0, "id", [f"r{i:03d}" for i in range(len(s))])
    s["wers_a"] = [_mark(by_line[r.line_a], r.word_a) for r in s.itertuples()]
    s["wers_b"] = [_mark(by_line[r.line_b], r.word_b) for r in s.itertuples()]
    sheet = s[["id", "kind", "wers_a", "wers_b"]].assign(rym="", uwagi="")
    key = s[["id", "kind", "type", "score", "syllables", "artist", "line_a", "word_a", "line_b", "word_b"]]
    return sheet, key


def figure_gold(n: int = 500, seed: int = 7) -> pd.DataFrame:
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    lines = lines[lines.attributed & ~lines.is_dup].sort_values(["song_id", "section", "line"]).reset_index(drop=True)
    prev_text = lines.groupby(["song_id", "section"]).text.shift(1).fillna("")
    next_text = lines.groupby(["song_id", "section"]).text.shift(-1).fillna("")
    lines = lines.assign(poprzedni=prev_text, nastepny=next_text)
    s = lines.sample(n, random_state=seed).reset_index(drop=True)
    s.insert(0, "id", [f"f{i:03d}" for i in range(len(s))])
    out = s[["id", "line_uid", "artist", "poprzedni", "text", "nastepny"]].rename(columns={"text": "wers"})
    for f in SHEET_FIGURES.values():
        out[f] = ""
    out["uwagi"] = ""
    return out


def label_studio_files(rhymes: pd.DataFrame, figures: pd.DataFrame) -> None:
    (GOLD / "ls_rymy_tasks.json").write_text(json.dumps(
        [{"data": {"id": r.id, "wers_a": r.wers_a, "wers_b": r.wers_b}} for r in rhymes.itertuples()],
        ensure_ascii=False, indent=1), encoding="utf-8")
    (GOLD / "ls_rymy_config.xml").write_text("""<View>
  <Header value="Czy zaznaczone słowa «…» się rymują (dokładnie, asonansem albo niedokładnie, tak jak słychać w rapie)?"/>
  <Text name="a" value="$wers_a"/>
  <Text name="b" value="$wers_b"/>
  <Choices name="rym" toName="a" choice="single" required="true">
    <Choice value="1" alias="rym"/>
    <Choice value="0" alias="nie rym"/>
  </Choices>
</View>
""", encoding="utf-8")
    (GOLD / "ls_figury_tasks.json").write_text(json.dumps(
        [{"data": {"id": r.id, "poprzedni": r.poprzedni, "wers": r.wers, "nastepny": r.nastepny}}
         for r in figures.itertuples()], ensure_ascii=False, indent=1), encoding="utf-8")
    choices = "\n".join(f'    <Choice value="{f}" hint="{h}"/>' for f, h in FIGURE_HELP.items())
    (GOLD / "ls_figury_config.xml").write_text(f"""<View>
  <Header value="Zaznacz figury w ŚRODKOWYM wersie (poprzedni i następny tylko dla kontekstu)"/>
  <Text name="poprzedni" value="$poprzedni"/>
  <Text name="wers" value="$wers"/>
  <Text name="nastepny" value="$nastepny"/>
  <Choices name="figury" toName="wers" choice="multiple">
{choices}
  </Choices>
</View>
""", encoding="utf-8")


def build() -> dict[str, int]:
    GOLD.mkdir(parents=True, exist_ok=True)
    sheet, key = rhyme_gold()
    figures = figure_gold()
    sheet.to_csv(GOLD / "rymy_do_oznaczenia.csv", sep=";", index=False, encoding="utf-8-sig")
    key.to_csv(GOLD / "rymy_klucz.csv", sep=";", index=False, encoding="utf-8-sig")
    figures.drop(columns="line_uid").to_csv(GOLD / "figury_do_oznaczenia.csv", sep=";", index=False, encoding="utf-8-sig")
    figures[["id", "line_uid"]].to_csv(GOLD / "figury_klucz.csv", sep=";", index=False, encoding="utf-8-sig")
    label_studio_files(sheet, figures)
    (GOLD / "INSTRUKCJA.md").write_text(
        "# Złoty zbiór – instrukcja\n\n"
        "Pliki do oznaczenia (Excel, separator `;`) albo Label Studio (`ls_*_tasks.json` + `ls_*_config.xml`).\n\n"
        "## rymy_do_oznaczenia.csv (300 par)\n"
        "W kolumnie `rym` wpisz 1, jeśli zaznaczone słowa «…» się rymują tak, jak słychać to w rapie "
        "(rym dokładny, asonans albo niedokładny), 0 jeśli nie. Pary są celowo wymieszane: część to rymy, część nie.\n\n"
        "## figury_do_oznaczenia.csv (500 wersów)\n"
        "Oceniasz kolumnę `wers`; `poprzedni` i `nastepny` są kontekstem. Wpisz 1 w kolumnie figury, która występuje:\n\n"
        + "\n".join(f"- `{f}`: {h}" for f, h in FIGURE_HELP.items())
        + "\n\nPuste pole = 0. Zapisz plik pod tą samą nazwą z dopiskiem `_ty` (np. `rymy_do_oznaczenia_ty.csv`).\n",
        encoding="utf-8")
    return {"rhyme_pairs": len(sheet), "lines": len(figures)}
