# mega-copy

This is a tool that helps to edit/refactor code in bulk. Useful when developing few similar features in your system

It works with:

1. Python files in "special" (Python-language specific) mode
2. "Other" files in "simple" (format-agnostic) mode

# Installation & Usage

1. Clone this repo:

```
git clone https://github.com/andrewboltachev/mega-copy.git
```

2. Create virtual environment:

```
mkvirtualenv mega-copy # (or use venv)
pip install -r requirements.txt
```

and a helper script to run the tool (e.g. `~/bin/mega-copy.sh`):

```bash
/home/andrey/.virtualenvs/mega-copy/bin/python /home/myuser/mega-copy/mega-copy.py $@
```

2. Suppose you want to refactor your Python code, replacing something called "property sale" to something else named "sales order". Run:

```
> mega.copy.sh pyshow property-sale sales-order
```

The tool will generate the following "replace map" (taking into account all possible spellings):

```python
{
    "propertysale": "salesorder",
    "property sale": "sales order",
    "property-sale": "sales-order",
    "property_sale": "sales_order",
    "PROPERTYSALE": "SALESORDER",
    "PROPERTY SALE": "SALES ORDER",
    "PROPERTY-SALE": "SALES-ORDER",
    "PROPERTY_SALE": "SALES_ORDER",
    "PropertySale": "SalesOrder",
    "Property Sale": "Sales Order",
    "Property-Sale": "Sales-Order",
    "Property_Sale": "Sales_Order",
    "Propertysale": "Salesorder",
    "Property sale": "Sales order",
    "Property-sale": "Sales-order",
    "Property_sale": "Sales_order",
    "propertySale": "salesOrder",
    "property Sale": "sales Order",
    "property-Sale": "sales-Order",
    "property_Sale": "sales_Order"
}
```

and below **show** all **Python** code expressions affected by it in code (your current directory)

Instead of `pyshow` you can then use another command — `pyren`, to rename all occurencies in the code in-place

## License

This project is licensed under the [MIT License](LICENSE).

## Sponsors

Visit [Evrone](https://evrone.com/) website to get more information about the [projects](https://evrone.com/cases) build.

<a href="https://evrone.com/?utm_source=postcss-px-to-viewport">
  <img src="https://user-images.githubusercontent.com/417688/34437029-dbfe4ee6-ecab-11e7-9d80-2b274b4149b3.png"
       alt="Sponsored by Evrone" width="231" />
</a>
