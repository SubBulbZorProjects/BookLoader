# Book Loader

![API](https://cdn.dribbble.com/users/68544/screenshots/2129380/book.png)

Book Loader tool.

## Install required packages

```pyhton
py -m pip install -r requirements.txt
```

## Configure .ini file [conf](config/conf.ini)

conf.ini is main configuration file of project.

**General** section:

* *image_folder* - allows you to select the path to download photos.

**Validator** section:

* *discard* - allows to specify strings which should be discarded.
* *priority* - allows to specify source which should be chosen as first.

**Category** section:

* *categories* - allows to specify list of categories.
* *threshold* - allows to specify threshold value for fuzzer. (larger value is more strict)

**ISBNdb** section:

ISBNdb is paid - [Plans](https://isbndb.com/isbn-database)

* *url* - is [ISBNdb](https://isbndb.com/) url.
* *token* - token allows using ISBNdb [API](https://isbndb.com/apidocs/v2).

**Google** - section:

Google API is free of charge.

* *url* is [Google Books](https://books.google.pl/) url.
* *token* - token allows using Google Books [API](https://developers.google.com/books/docs/v1/using).

**WooCommerce** section:

* *url* - is your **WooCommerce/WordPress** url, including http/s prefix.

    ```css
    https://{wordpress}
    ```

* *key* - is a *consumer key* generated from [WooCommerce](https://docs.woocommerce.com/document/woocommerce-rest-api/)
* *secret* - is a *private key* generated from [WooCommerce](https://docs.woocommerce.com/document/woocommerce-rest-api/)

**WordPress** section:

* *url* - is your **WooCommerce/WordPress** url, including http/s prefix and also path to WordPress API.

    ```css
    https://{wordpress}/wp-json/wp/v2
    ```

* *user* - is the name of the application generated from [WordPress](https://pl.wordpress.org/plugins/application-passwords/)
* *secret* - is a password generated from [WordPress](https://pl.wordpress.org/plugins/application-passwords/)

**MySQL** section:

* *host* - is your database server hostname or ip address.
* *user* - is user db user name.
* *password* - is password for db user.
* *database* - is your database name.

**Source** section:

The Source section allows you to decide which source should be used by the program.

* *isbndb* - Enable `True` or Disable `False` ISBNdb source.
* *google* - Enable `True` or Disable `False` Google Books source.
* *amazon* - Enable `True` or Disable `False` Amazon source.
* *goodreads* - Enable `True` or Disable `False` GoodReads source.

## Individual files

[book.py](book.py) is the core of project.

[book_loader.py](book_loader.py) is the PyQt5 GUI.

[image_downloader.py](image_downloader.py) as the name says, he gets a picture. **get_image** function requires a link to the image and the target name, the image is saved in the path indicated in the **[conf](config/conf.ini)** file -> **General** -> **image_folder**.

[woo.py](woo.py) is responsible for supporting the WooCommerce API.
The **main** function realizes the creation of a new product.
The **get_product** function allows you to retrieve information about an existing product.

[wp.py](wp.py) is responsible for supporting the WordPress API.
the **main** function allows you to upload an image to a media library.  
The image is uploaded as the full local path, the url is returned.

[database.py](database.py) is responsible for simple integration with MySQL, product search is much faster than with API.
