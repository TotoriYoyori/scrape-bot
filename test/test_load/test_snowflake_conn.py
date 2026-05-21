import snowflake.connector

def test_connection():
    with snowflake.connector.connect(
        user='TotoriYoyori',
        password='Mastercode#123',
        account='PDVGBNI-VYB14613',
        warehouse='COMPUTE_WH',
        database='LEAGUE_RECORDS',
        schema='L30_ID'
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * 
                FROM DIM_INTERVALS_KDA
                ORDER BY RANDOM(42)
                LIMIT 10; 
                """
            )
            df = pd.DataFrame(
                cur.fetchall(),
                columns=[col[0] for col in cur.description]
            )
            df.iloc[:, 0] = df.iloc[:, 0].apply(lambda x: x.hex().upper() if x else None)

    assert set(df.columns) == {'PLAYER_INTERVAL_ID', 'MINUTE', 'KILLS', 'DEATHS', 'ASSISTS'}
    assert len(df) == 10
    assert df.isna().sum().sum() == 0
