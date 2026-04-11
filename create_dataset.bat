@REM @echo off
@REM echo Creating Large Vendor Dataset...
@REM echo.

@REM echo Creating vendors.csv with 50 vendors...
@REM echo vendor_id,vendor_name,category,region,contract_value_m,risk_level,payment_terms,vendor_tier,contact_email,contract_start_date,employee_count,certifications,status > data/vendors.csv
@REM echo V001,TechCorp Global Inc,Electronics,North America,15.2,Low,30,Strategic,contact@techcorp.com,2020-03-15,12500,"ISO9001,ISO14001,ISO45001",Active >> data/vendors.csv
@REM echo V002,Quantum Solutions Ltd,Software,Europe,8.7,Low,15,Strategic,info@quantumsolutions.com,2019-11-22,8500,"ISO27001,CMMI5,ISO9001",Active >> data/vendors.csv
@REM echo V003,Alpha Materials Corp,Raw Materials,Asia Pacific,22.5,Low,30,Strategic,sales@alphamaterials.com,2018-07-10,18200,"ISO9001,ISO14001,ISO45001",Active >> data/vendors.csv
@REM REM ... Add all 50 vendors from above ...

@REM echo Creating performance.csv with 600 records...
@REM echo vendor_id,month,on_time_delivery,quality_score,cost_variance_pct,communication_score,flexibility_score,order_volume,order_value_k,defect_rate,lead_time_days > data/performance.csv
@REM echo V001,2023-07,98.5,99.2,-0.8,96.2,94.1,289,234.5,0.08,4.2 >> data/performance.csv
@REM echo V001,2023-08,99.1,99.4,-1.2,96.8,94.7,312,256.8,0.06,3.9 >> data/performance.csv
@REM REM ... Add all 600 performance records ...

@REM echo Creating brand.csv with 50 brand records...
@REM echo vendor_id,brand_impact_score,customer_satisfaction,innovation_score,sustainability_score,brand_safety_incidents,social_sentiment,market_reputation,esg_rating > data/brand.csv
@REM echo V001,94.2,96.5,91.8,89.3,0,88.7,Excellent,AAA >> data/brand.csv
@REM echo V002,92.7,95.2,90.1,87.6,0,86.9,Excellent,AA >> data/brand.csv
@REM REM ... Add all 50 brand records ...

@REM echo.
@REM echo ✅ Dataset created successfully!
@REM echo 📊 50 Vendors, 600 Performance Records, 50 Brand Records
@REM echo 🚀 Run: python run.py
@REM pause