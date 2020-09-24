#Deployment instructions

1. Clone repo:
    ```
    git clone https://github.com/deepmipt/log_analysis.git
    ```
2. `cd` log_analysis dir:
    ```
    cd log_analysis
    ```
3. Create and activate virtual env:
    ```
    virtualenv env -p python3.6
    source env/bin/activate
    ```
4. Install:
    ```
    python setup.py develop
    ```
5. Set Jupyter password:
    ```
    jupyter notebook password
    ```
6. Generate Jupyter config:
    ```
    jupyter notebook --generate-config
    ```
7. `cd` scripts dir:
    ```
    cd scripts
    ```
8. Run deployment script:
    ```
    python deploy.py 
    ```
9. `cd` back to log_analysis dir and run launch script:
    ```
    cd ..
    ./run_log_analysis.sh
    ```
10. To create update task:
    1. Open crontab editor with:
        ```
        crontab -e
        ```
    2. Add task according following mask:
        ```
        * * * * * cd </path/to/dir/where/to/store/update/logs> && </path/to/python> </path/to/update.py>
        ```

###Commands for Django
```
python manage.py createsuperuser
python manage.py runserver
python manage.py makemigrations stats
python manage.py migrate
python manage.py shell
```