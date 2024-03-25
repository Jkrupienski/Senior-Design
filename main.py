import os
import pandas as pd
import zipfile

from pathlib import Path

from arcgis.gis import GIS
from arcgis.learn import RetinaNet, prepare_data

gis = GIS('home')
training_data = gis.content.get('ccaa060897e24b379a4ed2cfd263c15f')
training_data

filepath = training_data.download(file_name=training_data.name)


with zipfile.ZipFile(filepath, 'r') as zip_ref:
    zip_ref.extractall(Path(filepath).parent)

data_path = Path(os.path.join(os.path.splitext(filepath)[0]))


data = prepare_data(data_path,
                    batch_size=4,
                    dataset_type="PASCAL_VOC_rectangles",
                    chip_size=480)

data.classes
data.show_batch()