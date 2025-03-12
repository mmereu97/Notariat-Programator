# Programator Acte Notariale

O aplicație desktop pentru gestionarea și programarea actelor notariale, dezvoltată în Python cu PyQt5.

## Descriere
Programator Acte Notariale este o aplicație pentru birouri notariale care permite gestionarea eficientă a programărilor și actelor notariale. Aplicația oferă o interfață intuitivă de tip calendar săptămânal, cu posibilitatea de a adăuga, edita și șterge programări pentru clienți.

## Funcționalități

### Gestionare programări

- **Calendar săptămânal:** Vizualizarea programărilor pe zile și ore
- **Adăugare programări:** Programare rapidă cu specificarea clientului și tipului de document
- **Editare programări:** Posibilitatea de a modifica detaliile unei programări existente
- **Ștergere programări:** Ștergerea programărilor direct din fereastra de editare
- **Observații:** Adăugare de observații pentru fiecare programare
- **Programări cu ore flexibile:** Nu doar la ore fixe
- **Marcarea timpului liber:** Tip special "Liber" cu evidențiere vizuală distinctă
- **Evidențierea zilei curente:** Culoare specială pentru ziua curentă

### Organizare tipuri de documente

- **Gestionare tipuri documente:** Listă configurabilă de tipuri de acte notariale
- **Sistem de culori personalizabile:** 4 culori configurabile pentru diferite tipuri de documente
- **Redenumire facilă:** Redenumire tipuri de documente cu dublu-click
- **Sortare alfabetică:** Ordonare automată alfabetică a tipurilor de documente
- **Actualizare automată:** La redenumirea unui tip de document, toate programările se actualizează

### Navigare și informații

- **Butoane de navigare:** Navigare rapidă între săptămâni (anterior/următor)
- **Dialog calendar:** Salt rapid la orice dată din calendar
- **Curs valutar BNR:** Afișare curs Euro-Lei actualizat automat
- **Evidențierea modificărilor:** Istoric complet al creării și modificărilor

### Securitate și sincronizare

- **Prevenire conflicte:** Blocarea deschiderii simultane a aplicației pe mai multe stații
- **Detecție blocaje vechi:** Auto-detectare și eliminare a blocajelor mai vechi de 4 ore
- **Opțiune de forțare:** Posibilitate de a forța deschiderea în cazuri excepționale

## Tehnologii utilizate

- **Python 3.x:** Limbajul de programare principal
- **PyQt5:** Framework pentru interfața grafică
- **SQLite:** Bază de date pentru stocarea programărilor
- **JSON:** Format pentru salvarea configurațiilor de tipuri de documente
- **Requests & BeautifulSoup4:** Pentru preluarea cursului valutar BNR

## Instalare

### Pași de instalare
```bash
# Clonați repository-ul:
git clone https://github.com/utilizator/programator-acte-notariale.git
cd programator-acte-notariale

# Instalați dependențele:
pip install -r requirements.txt
# sau direct
pip install PyQt5 requests beautifulsoup4

# Rulați aplicația:
python programator.py
```

## Ghid de utilizare

### Navigare în calendar

- Folosiți butoanele ← și → pentru a naviga între săptămâni
- Apăsați butonul **Calendar** pentru a sări direct la o dată specifică
- Ziua curentă este evidențiată automat cu o culoare distinctivă

### Adăugare programare

- Apăsați butonul + de lângă ora dorită
- Completați detaliile clientului și tipul documentului
- Adăugați observații dacă este necesar
- Apăsați **Salvează**

### Editare programare

- Apăsați butonul **Edit** de lângă programarea existentă
- Modificați detaliile necesare
- Apăsați **Salvează** pentru a confirma modificările sau **Șterge programare** pentru a elimina programarea

### Gestionare tipuri de documente

- Apăsați butonul **Adaugă tip document**
- Selectați culoarea dorită pentru fiecare tip de document din lista de opțiuni
- Pentru redenumire, faceți dublu-click pe numele tipului de document
- Pentru a adăuga un nou tip, completați câmpul și apăsați **Adaugă**
- Folosiți butonul **Configurare Culori** pentru a personaliza paleta de culori disponibile
- Apăsați **Salvează** pentru a confirma modificările

### Utilizare în rețea

- Aplicația detectează automat dacă este deschisă pe altă stație din rețea
- În caz de blocare accidentală, folosiți opțiunea **Forțează deschidere**

## Structura bazei de date
Aplicația folosește SQLite pentru stocarea datelor în fișierul notarial_scheduler.db. Structura include:

- **Tabelul appointments** - stochează toate programările, inclusiv istoricul de modificări
- **Fișierul document_types.json** - conține configurația pentru tipurile de documente și culorile asociate

## Contribuție
Contribuțiile sunt binevenite! Pentru a contribui la acest proiect:

- Fork-ați repository-ul
- Creați un branch nou: `git checkout -b feature/functionalitate-noua`
- Faceți modificările dorite
- Commit-ați modificările: `git commit -m 'Adăugare funcționalitate nouă'`
- Push la branch: `git push origin feature/functionalitate-noua`
- Creați un Pull Request

## Licență
Acest proiect este freeware

## Autor și Contact
- Creat de Mihai Mereu
- Pentru întrebări sau sugestii, contactați: mihaimereu97@gmail.com
