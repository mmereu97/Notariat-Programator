# Programator Acte Notariale
O aplicație desktop pentru gestionarea și programarea actelor notariale, 
dezvoltată în Python cu PyQt5.

## Descriere

Programator Acte Notariale este o aplicație pentru birouri notariale care
permite gestionarea eficientă a programărilor și actelor notariale. 
Aplicația oferă o interfață intuitivă de tip calendar săptămânal, cu 
posibilitatea de a adăuga, edita și șterge programări pentru clienți.

## Funcționalități

- **Calendar săptămânal:** Vizualizarea programărilor pe zile și ore
- **Adăugare programări:** Programare rapidă cu specificarea clientului și tipului de document
- **Editare programări:** Posibilitatea de a modifica detaliile unei programări existente
- **Ștergere programări:** Ștergerea programărilor direct din fereastra de editare
- **Observații:** Adăugare de observații pentru fiecare programare
- **Evidențiere tipuri documente:** Anumite tipuri de documente pot fi evidențiate pentru o vizualizare mai ușoară
- **Programări de tip "Liber":** Marcarea timpului liber cu culori specifice
- **Istoric modificări:** Păstrarea informațiilor despre crearea și modificarea programărilor
- **Navigare rapidă:** Butoane pentru navigare săptămânală și calendar pentru salt la date specifice

## Tehnologii utilizate

- **Python 3.x:** Limbajul de programare principal
- **PyQt5:** Framework pentru interfața grafică
- **SQLite:** Bază de date pentru stocarea programărilor
- **JSON:** Format pentru salvarea configurațiilor de tipuri de documente

## Instalare
## Cerințe preliminare

Python 3.6 sau mai recent
PyQt5

## Pași de instalare

Clonați repository-ul:

```bash
git clone https://github.com/utilizator/programator-acte-notariale.git
cd programator-acte-notariale
```

Instalați dependențele:

```bash
pip install -r requirements.txt
```

Rulați aplicația:

```bash
python programator.py
```

## Ghid de utilizare

## Navigare în calendar

Folosiți butoanele ← și → pentru a naviga între săptămâni
Apăsați butonul Calendar pentru a sări direct la o dată specifică

## Adăugare programare

Apăsați butonul + de lângă ora dorită
Completați detaliile clientului și tipul documentului
Apăsați Salvează

## Editare programare

Apăsați butonul Edit de lângă programarea existentă
Modificați detaliile necesare
Apăsați Salvează pentru a confirma modificările sau Șterge programare pentru a elimina programarea

## Gestionare tipuri de documente

Apăsați butonul Adaugă tip document
Bifați tipurile de documente care trebuie evidențiate cu fundal verde
Pentru a adăuga un nou tip, completați câmpul și apăsați Adaugă
Apăsați Salvează pentru a confirma modificările

## Structura bazei de date
Aplicația folosește SQLite pentru stocarea datelor în fișierul notarial_scheduler.db. Structura principală include:

Tabelul appointments - stochează toate programările
Fișierul document_types.json - conține configurația pentru tipurile de documente

## Actualizări recente

Adăugare buton de ștergere în dialogul de editare programare
Îmbunătățirea gestionării tipurilor de documente evidențiate
Adăugarea câmpului de observații pentru programări
Implementarea istoricului modificărilor pentru programări

## Contribuție
Contribuțiile sunt binevenite! Pentru a contribui la acest proiect:

Fork-ați repository-ul
Creați un branch nou: git checkout -b feature/functionalitate-noua
Faceți modificările dorite
Commit-ați modificările: git commit -m 'Adăugare funcționalitate nouă'
Push la branch: git push origin feature/functionalitate-noua
Creați un Pull Request

## Licență
Acest proiect este freeware

## Contact
Pentru întrebări sau sugestii, contactați: mihaimereu97@gmail.com
