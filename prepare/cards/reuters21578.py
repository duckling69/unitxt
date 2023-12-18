from datasets import get_dataset_config_names

from src.unitxt import add_to_catalog
from src.unitxt.blocks import (
    AddFields,
    FormTask,
    InputOutputTemplate,
    LoadHF,
    RenameFields,
    SplitRandomMix,
    TaskCard,
    TemplatesList,
)
from src.unitxt.test_utils.card import test_card

dataset_name = "reuters21578"

classlabels = {
    "ModApte": [
        "acq",
        "alum",
        "austdlr",
        "barley",
        "bop",
        "can",
        "carcass",
        "castor-oil",
        "castorseed",
        "citruspulp",
        "cocoa",
        "coconut",
        "coconut-oil",
        "coffee",
        "copper",
        "copra-cake",
        "corn",
        "corn-oil",
        "cornglutenfeed",
        "cotton",
        "cotton-oil",
        "cottonseed",
        "cpi",
        "cpu",
        "crude",
        "cruzado",
        "dfl",
        "dkr",
        "dlr",
        "dmk",
        "earn",
        "f-cattle",
        "fishmeal",
        "fuel",
        "gas",
        "gnp",
        "gold",
        "grain",
        "groundnut",
        "groundnut-oil",
        "heat",
        "hog",
        "housing",
        "income",
        "instal-debt",
        "interest",
        "inventories",
        "ipi",
        "iron-steel",
        "jet",
        "jobs",
        "l-cattle",
        "lead",
        "lei",
        "lin-meal",
        "lin-oil",
        "linseed",
        "lit",
        "livestock",
        "lumber",
        "meal-feed",
        "money-fx",
        "money-supply",
        "naphtha",
        "nat-gas",
        "nickel",
        "nkr",
        "nzdlr",
        "oat",
        "oilseed",
        "orange",
        "palladium",
        "palm-oil",
        "palmkernel",
        "peseta",
        "pet-chem",
        "platinum",
        "plywood",
        "pork-belly",
        "potato",
        "propane",
        "rand",
        "rape-meal",
        "rape-oil",
        "rapeseed",
        "red-bean",
        "reserves",
        "retail",
        "rice",
        "ringgit",
        "rubber",
        "rupiah",
        "rye",
        "saudriyal",
        "sfr",
        "ship",
        "silver",
        "skr",
        "sorghum",
        "soy-meal",
        "soy-oil",
        "soybean",
        "stg",
        "strategic-metal",
        "sugar",
        "sun-meal",
        "sun-oil",
        "sunseed",
        "tapioca",
        "tea",
        "tin",
        "trade",
        "veg-oil",
        "wheat",
        "wool",
        "wpi",
        "yen",
        "zinc",
    ]
}
classlabels["ModLewis"] = classlabels["ModApte"]
classlabels["ModHayes"] = sorted(classlabels["ModApte"] + ["bfr", "hk"])

for subset in get_dataset_config_names(dataset_name):
    card = TaskCard(
        loader=LoadHF(path=f"{dataset_name}", name=subset),
        preprocess_steps=[
            SplitRandomMix(
                {"train": "train[85%]", "validation": "train[15%]", "test": "test"}
            ),
            RenameFields(field_to_field={"topics": "labels"}),
            AddFields(
                fields={
                    "classes": classlabels[subset],
                    "text_type": "text",
                    "type_of_class": "topic",
                }
            ),
        ],
        # TODO we need multi_label template and then switch to multi_label task
        task=FormTask(
            inputs=["text"],
            outputs=["labels"],
            metrics=["metrics.f1_micro", "metrics.accuracy", "metrics.f1_macro"],
        ),
        templates=TemplatesList(
            [
                InputOutputTemplate(
                    input_format="{text}",
                    output_format="{labels}",
                ),
            ]
        ),
        #        templates="templates.classification.multi_class.all",
    )
    test_card(card, debug=False)
    add_to_catalog(card, f"cards.{dataset_name}.{subset}", overwrite=True)
