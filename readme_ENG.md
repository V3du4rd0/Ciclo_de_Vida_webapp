# Ciclo de Vida
## WebApp

[SPA](readme.md)

This app is designed for teaching and exploring qualitative life cycle analysis in design-related fields. It includes three main operational functions: describing manufacturing processes in terms of their inputs and outputs, calculating environmental flow vectors, and querying a database.

Unlike other Life Cycle Assessment software, this app features an intuitive interface. However, the current version includes only the three functions mentioned above. A menu provides access to its two modes of use: setting manufacturing processes from scratch (via the New Project button), or performing an analysis using one of the three provided examples, which can also be edited.

The theoretical basis of the calculations implemented in this app relies on a system of equations defined by three arrays: a technology matrix, an intervention matrix, and a demand vector. The following reference was used as the foundation for this formulation:

Heijungs, R., & Suh, S. (2002). _The Computational Structure of Life Cycle Assessment_ (S. Suh, Ed.). Springer Netherlands.


### Requirements

This web app requires:

* Web browser.
* Python 3.
* Internet connection.

In addition to Python, all dependencies listed in the `requirements.txt` file must be installed. These dependencies can be installed by executing the following command within the Python environment:

```
pip install -r requirements.txt
```

### Downloading the Databases

This app requires two environmental impact databases: TRACI and CML-IA.

**Option 1** (Windows and Linux)

The repository includes two download scripts:

 * **win_db_downloader.bat**
 * **linux_db_downloader.sh**

 Each script is specific to the operating system indicated in its name. When executed, the script automatically create a directory named `databases` and download the databases into it.

**Option 2** (Manual downloading)

1) Copy and paste the following URLs into the address bar of a web browser:

```
http://www.leidenuniv.nl/cml/ssp/databases/cmlia/cmlia.zip

https://www.epa.gov/system/files/documents/2024-01/traci_2_2.xlsx
```

2) Create a folder named **databases** within this directory. Copy the xlsx file and the contents of the zip file into this folder. The final databases folder should contain the following files:

```
├── databases
│		├── CML-IA_aug_2016.xls
│		├── CML-IA_august_2016_update_info.xls
│		└── traci_2_2.xlsx
```

### Usage

1) Once the prerequisites are installed and the database downloaded, start the Flask server used by this app uses. The easiest way is to open a terminal (or PowerShell on Windows) in this project directory and run the following command:

```
flask run --host=0.0.0.0 --port=5000
```

2) Open the `index.html` file in any web browser.

3) The app includes three examples that demonstrate its functionality.

### Gallery

<table>
  <tr>
    <td>
      <!-- Im 1 -->
      <img src="Gallery/img01.png" alt="" width="200">
    </td>
    <td>
      <!-- Im 2 -->
      <img src="Gallery/img02.png" alt="" width="200">
    </td>
    <td>
      <!-- Im 3 -->
      <img src="Gallery/img03.png" alt="" width="200">
    </td>
    <td>
      <!-- Im 4 -->
      <img src="Gallery/img07.png" alt="" width="200">
    </td>
  </tr>
</table>


### Licensing

WebApp distribution under GNU2 license.

This project depends on the following third-party libraries:

* Chart.js (static/js/char.min.js)
* MathJax (static/js/mathjax)
* Numeric.js (static/js/numeric.min.js)

Copies of their corresponding license files are included in the LICENSES directory.