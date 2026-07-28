# PMET
PMET — Point-based Model Evaluation Tool

PMET is a cell segmentation model evaluation tool, built to evaluate segmentation
model results without requiring a manually generated segmentation mask as a ground truth.

## Inputs

PMET takes a path to a single **input directory**. This directory is searched recursively and files may be organized
into subdirectories in any structure.

The input directory must contain two types of files:

### 1. Labeled mask files (`.tif`)

Segmentation masks to evaluate, provided as **labeled masks**: each cell's pixels should be assigned a
unique integer ID, distinguishing it from other cells in the image. Background pixels have
the value `0`.

#### File naming pattern

```{image_name}.ome.tif - Image{n}_{model_name}_label.tif```

**Example:** `CellDIVE_SLIDE-123_A-1.ome.tif - Image0_cellpose_label.tif`

| Field          | Description                                                            |
|----------------|------------------------------------------------------------------------|
| `{image_name}` | Name of the original image (matches the corresponding `.ome.tif` file) |
| `{n}`          | Image index number (optional, may be omitted)                          |
| `{model_name}` | Name of the model used to generate the mask                            |

### 2. GeoJSON annotation files (`.geojson`)

Annotation data exported from QuPath, corresponding to each sample.

#### File naming pattern

```{image_name}.ome.tif - Image{n}.geojson```

**Example:** `CellDIVE_SLIDE-123_A-1.ome.tif - Image1.geojson`

| Field          | Description                                                                                      |
|----------------|--------------------------------------------------------------------------------------------------|
| `{image_name}` | Name of the original image. Must exactly match `{image_name}` in the corresponding mask filename |
| `{n}`          | Image index number (optional)                                                                    |

#### Required annotation types

| Annotation Type   | Geometry Type | Description                                                                                   |
|-------------------|---------------|-----------------------------------------------------------------------------------------------|
| Sample area       | `Polygon`     | Defines the region of the mask included in evaluation. Exactly one per file. `properties.classification.name` must equal `"cell_segmentation_sample_area"`. |
| Point annotations | `MultiPoint`  | Marks the center of each ground-truth cell. All `MultiPoint` features in the file are treated as point annotations. |

## Outputs

Outputs are written to the directory specified with `-o`/`--output`. If none is specified,
outputs are written to a directory alongside the input directory.

PMET produces two outputs per sample:

### 1. Scores CSV file

One CSV file, with one row per evaluated sample.

| Column          | Type   | Description                                             |
|-----------------|--------|---------------------------------------------------------|
| Image Name      | string | Name of the original image the mask was generated for   |
| Points File     | string | GeoJSON file associated with this sample                |
| Mask File       | string | `.tif` file containing the labeled mask for this sample |
| Model Name      | string | Model that produced the segmentation mask               |
| True Positives  | int    | Cells correctly identified                              |
| False Positives | int    | Cells incorrectly detected                              |
| False Negatives | int    | Ground-truth cells the model failed to detect           |
| Precision       | float  | Precision score for this sample                         |
| Recall          | float  | Recall score for this sample                            |
| F1              | float  | Combined precision/recall score for this sample         |

> [!NOTE]
> **Undersegmented cells:** when two or more ground-truth points fall within a single detected cell region,
> one point is counted as a True Positive and the remaining points are counted as False Negatives.


### 2. Accuracy overlay image

A visual copy of the original mask, color-coded by accuracy, containing three elements:

- Cell regions, colored by prediction accuracy
- Ground-truth points, colored by detection accuracy
- The sample border, drawn as a red line

#### Point color scheme

| Color | Meaning                                                              |
|-------|----------------------------------------------------------------------|
| Green | Cell correctly segmented                                             |
| Red   | Cell missed / not identified                                         |
| Blue  | Cell undersegmented (incorrectly merged with a neighboring cell)     |
| Grey  | Cell is clipped by the sample border; excluded from accuracy metrics |

#### Cell color scheme

| Color | Meaning                                                              |
|-------|----------------------------------------------------------------------|
| Green | Detection accurately segments one cell                               |
| Red   | Cell incorrectly identified where none exists                        |
| Blue  | Multiple cells incorrectly detected as one                           |
| Grey  | Cell is clipped by the sample border; excluded from accuracy metrics |

> [!NOTE]
> The overlay image is a quick visual reference only. For detailed inspection, use the
> original image and mask files directly.

## Scoring algorithm

For each sample, predicted cell regions (from the mask) are matched against user-placed
ground-truth points to compute accuracy.

### Processing steps

1. Each ground-truth point is associated with the predicted cell region it falls within.
2. Cell regions touching the sample border are detected and, along with any points
   associated with them, excluded from scoring.
3. Precision, Recall, and F1 are calculated from the remaining cells.

### Classification rules

| Outcome            | Condition                                                         |
|--------------------|-------------------------------------------------------------------|
| True Positive      | Exactly one ground-truth point falls within the cell region       |
| False Positive     | No ground-truth point falls within the cell region                |
| False Negative     | A ground-truth point does not fall within any labeled cell region |
| Undersegmented     | Two or more ground-truth points fall within a single cell region. Scored as one True Positive plus a False Positive for each additional point |
| Clipped (excluded) | The cell region touches or extends beyond the sample border       |

### Metric formulas

- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **F1** = 2 × (Precision × Recall) / (Precision + Recall)

# Installing

## Option 1: Apptainer container (recommended)

### Prerequisites
- Apptainer 1.5+

### Getting the container

**Download pre-built:** grab the `.sif` file from [Releases](https://github.com/GPEC/pmet/releases).

**Or build locally:**
```bash
git clone https://github.com/GPEC/pmet.git
cd pmet/apptainer
apptainer build pmet.sif pmet.def
```

### Run
```bash
apptainer run pmet.sif --help
```

## Option 2: Run locally

### Prerequisites
- Python 3.14+
- pip
  

1. Clone the repository.
```bash
git clone https://github.com/GPEC/pmet.git
cd pmet
```
2. Create a virtual environment.
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Install the dependancies.
```bash
pip install -r requirements.txt
```
4. Run
```bash
python pmet.py --help
```

# Usage

Run with the Apptainer container or directly with Python.

```bash
apptainer run pmet.sif -i [/path/to/input] -o [/path/to/output]
```

## Options

| Option                | Description                                     |
|-----------------------|-------------------------------------------------|
| `-h`, `--help`        | Show the help message and exit                  |
| `-i`, `--input`       | **(Required)** Input directory                  |
| `-o`, `--output`      | Output directory                                |
| `-w`, `--workers`     | Maximum number of parallel processors           |
| `-p`, `--padding`     | Number of pixels to shrink the sample border by |
| `-n`, `--no-progress` | Disable the progress bar                        |
