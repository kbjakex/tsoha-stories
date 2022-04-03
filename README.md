# tsoha-stories

Sovelluksessa voi luoda uusia tarinoita tai jatkaa toisten aloittamia. Etusivulla näkyy lista aloitetuista tarinoista, joiden takaa löytyy linkkejä tarinan jatko-osiin. Jokainen käyttäjä on peruskäyttäjä tai ylläpitäjä.

Sovelluksen ominaisuuksia:
* Käyttäjä voi kirjautua sisään ja ulos sekä luoda uuden tunnuksen.
* Käyttäjä näkee etusivulla listan kaikista alotetuista tarinoista, niiden julkaisuhetken, julkaisijan ja tykkäysten määrän.
* Käyttäjä voi luoda uuden tarinan antamalla otsikon ja alun, jonka maksimipituus on 256 merkkiä.
* Käyttäjä voi luoda jatkon olemassa olevalle tarinalle avaamalla tarinan tai sen jatko-osan, jolle haluaa kirjoittaa jatkon. Jatkon maksimipituus on 256 merkkiä.
* Käyttäjä voi muokata tai poistaa julkaisemiaan tekstinpätkiä, jos julkaisusta on kulunut alle puoli tuntia.
* Käyttäjä voi tykätä muiden julkaisemia tarinan alkuja tai jatko-osia. Käyttäjä voi antaa maksimissaan yhden tykkäyksen julkaisua kohden.
* Käyttäjä voi järjestää etusivulla näkemänsä tarinat tykkäysten, julkaisuajan tai julkaisijan perusteella.
* Ylläpitäjä voi poistaa julkaisuja.

## Building

```bash
git clone https://github.com/kbjakex/tsoha-stories/
cd tsoha-stories
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```