# Serpents

## Opis projektu
Serpents to gra dwuosobowa, oparta na Snake'u. Każdy gracz steruje jednym wężem morskim.

### Sterowanie
Węże pozostają w ciągłym ruchu. Gracze mogą jedynie zmieniać kierunek poruszania się węża zgodnie z poniższą tabelą:

| Kierunek | Gracz 1 | Gracz 2 |
|----------|---------|---------|
| Góra     | W       | I       |
| Dół      | S       | K       |
| Lewo     | A       | J       |
| Prawo    | D       | L       |

### Ryby
W losowych miejscach na planszy pojawiają się ryby. Kiedy wąż zje rybę, wydłuża się o jeden segment.

### Śmierć węża
Wąż ginie, jeśli jego głowa zderzy się z krawędzią planszy, swoim ogonem lub drugim wężem. Takie zdarzenie kończy rundę, a na ekranie pojawia się nazwa pozostającego przy życiu węża (lub informacja o remisie). Następnie plansza resetuje się, w celu rozpoczęcia nowej rundy. <br />
Węże mają określoną liczbę żyć. Gdy ta spadnie do zera, gra się kończy, a na ekranie pojawia się informacja o zwycięzcy (lub o przegranej obu graczy, w przypadku remisu).

## Wizualizacja gry
![wonsze](https://github.com/letHerCook/SO2-proj/assets/163906347/51f02fab-58e8-4835-9bdb-f858ff07212c)


## Wątki
- control_s1 - sterowanie pierwszym wężem
- control_s2 - sterowanie drugim wężem
- move_s1 - poruszanie pierwszym wężem
- move_s2 - poruszanie drugim wężem
- spawner - pojawianie się ryb na planszy
- is_round_over - sprawdzanie, czy runda się zakończyła

## Sekcje krytyczne
- lock_check_position - mutex
- cond_move - zmienna warunkowa
- lock_fish - mutex

