# Cura V2Neo Thumbnail creator
# Ken Huffman (huffmancoding@gmail.com)
#
# This only works with Cura 5.0 or later
# Based on:
# https://github.com/Ultimaker/Cura/blob/master/plugins/PostProcessingPlugin/scripts/CreateThumbnail.py

import base64

from UM.Logger import Logger
from cura.Snapshot import Snapshot
from cura.CuraVersion import CuraVersion

from ..Script import Script


class CreateV2NeoThumbnail(Script):
    def __init__(self):
        super().__init__()

    def _createSnapshot(self, width, height):
        Logger.log("d", "Creating thumbnail image...")
        try:
            return Snapshot.snapshot(width, height)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")

    def _encodeSnapshot(self, snapshot):
        Major=0
        try:
          Major = int(CuraVersion.split(".")[0])
        except:
          pass

        if Major < 5 :
          from PyQt5.QtCore import QByteArray, QIODevice, QBuffer
        else :
          from PyQt6.QtCore import QByteArray, QIODevice, QBuffer

        Logger.log("d", "Encoding thumbnail image...")
        try:
            thumbnail_buffer = QBuffer()
            if Major < 5 :
              thumbnail_buffer.open(QBuffer.ReadWrite)
            else:
              thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            thumbnail_image = snapshot
            thumbnail_image.save(thumbnail_buffer, "JPG")
            thumbnail_data = thumbnail_buffer.data()
            thumbnail_length = thumbnail_data.length()
            base64_bytes = base64.b64encode(thumbnail_data)
            base64_message = base64_bytes.decode('ascii')
            thumbnail_buffer.close()
            Logger.log("d", "Snapshot thumbnail_length={}".format(thumbnail_length))
            return (base64_message, thumbnail_length)
        except Exception:
            Logger.logException("w", "Failed to encode snapshot image")

    def _convertSnapshotToGcode(self, thumbnail_length, encoded_snapshot, width, height, chunk_size=76):
        Logger.log("d", "Converting snapshot into gcode...")
        gcode = []

        # these numbers appear to be related to image size, guessing here
        x1 = (int)(width/80) + 1
        x2 = width - x1
        header = "; jpg begin {}*{} {} {} {} {}".format(
            width, height, thumbnail_length, x1, x2, 500)
        Logger.log("d", "Gcode header={}".format(header))
        gcode.append(header)

        chunks = ["; {}".format(encoded_snapshot[i:i+chunk_size])
                  for i in range(0, len(encoded_snapshot), chunk_size)]
        gcode.extend(chunks)

        gcode.append("; jpg end")
        gcode.append(";")
        gcode.append("")

        return gcode

    def getSettingDataString(self):
        return """{
            "name": "Create V2Neo Thumbnail",
            "key": "CreateV2NeoThumbnail",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "width":
                {
                    "label": "Width",
                    "description": "Width of the generated thumbnail",
                    "unit": "px",
                    "type": "int",
                    "default_value": 200,
                    "minimum_value": "0",
                    "minimum_value_warning": "12",
                    "maximum_value_warning": "800"
                },
                "height":
                {
                    "label": "Height",
                    "description": "Height of the generated thumbnail",
                    "unit": "px",
                    "type": "int",
                    "default_value": 200,
                    "minimum_value": "0",
                    "minimum_value_warning": "12",
                    "maximum_value_warning": "600"
                }
            }
        }"""

    def execute(self, data):
        width = self.getSettingValueByKey("width")
        height = self.getSettingValueByKey("height")
        Logger.log("d", "CreateV2NeoThumbnail Plugin start with width={}, height={}...".format(width, height))

        snapshot = self._createSnapshot(width, height)
        if snapshot:
            Logger.log("d", "Snapshot created")
            (encoded_snapshot, thumbnail_length) = self._encodeSnapshot(snapshot)
            snapshot_gcode = self._convertSnapshotToGcode(
                thumbnail_length, encoded_snapshot, width, height)

            Logger.log("d", "Layer count={}".format(len(data)))
            if len(data) > 0:
                # The Ender-3 V2 Neo really wants this at the top of the file
                layer_index = 0
                lines = data[layer_index].split("\n")
                Logger.log("d", "Adding snapshot gcode lines (len={}) before '{}'".format(len(snapshot_gcode), lines[0]))
                lines[0:0] = snapshot_gcode
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines

        Logger.log("d", "CreateV2NeoThumbnail Plugin end")
        return data
