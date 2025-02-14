# coding=utf-8
# Copyright 2018-2023 EvaDB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pandas as pd

from evadb.catalog.catalog_type import Dimension, NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe
from evadb.utils.generic_utils import try_to_import_faiss


class Similarity(AbstractFunction):
    def _get_distance(self, numpy_distance):
        return numpy_distance[0][0]

    def setup(self):
        try_to_import_faiss()
        pass

    @property
    def name(self):
        return "Similarity"

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=[
                    "open_feat_np,* as open_feat_np",
                    "base_feat_np,* as base_feat_np",
                ],
                column_types=[NdArrayType.UINT8, NdArrayType.UINT8],
                column_shapes=[
                    (3, Dimension.ANYDIM, Dimension.ANYDIM),
                    (3, Dimension.ANYDIM, Dimension.ANYDIM),
                ],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["distance"],
                column_types=[NdArrayType.FLOAT32],
                column_shapes=[(32, 7)],
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get similarity score between two feature vectors: 1. feature vector of an opened image;
        and 2. feature vector from base table.
        """

        def _similarity(row: pd.Series) -> float:
            open_feat_np, base_feat_np = row["open_feat_np"], row["base_feat_np"]

            # TODO: currently system takes care of feature vector shape
            # transformation. Improve this later on.
            # Transform to 2D.
            open_feat_np = open_feat_np.reshape(1, -1)
            base_feat_np = base_feat_np.reshape(1, -1)
            import faiss

            distance_np = faiss.pairwise_distances(open_feat_np, base_feat_np)

            return self._get_distance(distance_np)

        ret = pd.DataFrame()
        ret["distance"] = df.apply(_similarity, axis=1)
        return ret
