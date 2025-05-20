# __manifest__.py
{
    'name': 'ArabInk Retention Management / إدارة استقطاعات الضمان لحبر العرب التجارية',
    'version': '16.0.1.0',
    'category': 'Accounting',
    'summary': 'Advanced retention management for ArabInk invoices and sales orders / إدارة متقدمة لاستقطاعات الضمان للفواتير وأوامر البيع لحبر العرب التجارية',
    'description': '''
# ArabInk Retention Management / إدارة استقطاعات الضمان لحبر العرب التجارية

A complete solution for managing retention amounts on sales orders and invoices at ArabInk.
حل متكامل لإدارة مبالغ استقطاعات الضمان على أوامر البيع والفواتير في حبر العرب التجارية.

## Features / الميزات

* **Flexible Retention Calculation**: Choose between percentage-based or fixed amount retention
* **حساب مرن للاستقطاعات**: اختر بين استقطاع بنسبة مئوية أو بمبلغ ثابت
* **Complete Lifecycle Management**: Track retentions from draft to confirmation, holding, and release
* **إدارة كاملة لدورة الحياة**: تتبع الاستقطاعات من المسودة إلى التأكيد والاحتجاز والإطلاق
* **Automatic Accounting Integration**: Generate proper accounting entries for retentions and releases
* **تكامل محاسبي تلقائي**: إنشاء قيود محاسبية صحيحة للاستقطاعات والإفراجات
* **Customizable Release Process**: Release retentions in full or in parts with complete audit trail
* **عملية إفراج قابلة للتخصيص**: إطلاق الاستقطاعات بالكامل أو بأجزاء مع سجل تدقيق كامل
* **Powerful Reporting**: Generate comprehensive reports to track retention status
* **تقارير قوية**: إنشاء تقارير شاملة لتتبع حالة الاستقطاعات
* **Multi-company Support**: Configure different retention settings for different entities
* **دعم متعدد الشركات**: تكوين إعدادات استقطاع مختلفة لكيانات مختلفة
* **Scheduled Release**: Automatically release retentions after specified periods
* **إطلاق مجدول**: إطلاق الاستقطاعات تلقائيًا بعد فترات محددة

## How to Use / كيفية الاستخدام

### 1. Configuration / الإعداد

**Configure Retention Settings / إعداد الاستقطاعات**:
* Go to Accounting → Configuration → Settings
* انتقل إلى المحاسبة ← الإعدادات ← الإعدادات
* Scroll to the "Retention Management" section
* انتقل إلى قسم "إدارة الاستقطاعات"
* Set default retention percentage (typically 5-10%)
* حدد نسبة الاستقطاع الافتراضية (عادة 5-10%)
* Select the retention account (create a dedicated liability account if needed)
* اختر حساب الاستقطاع (قم بإنشاء حساب التزام مخصص إذا لزم الأمر)
* Choose the accounting journal for retention transactions
* اختر دفتر اليومية المحاسبي لمعاملات الاستقطاع

**Set Up User Access / إعداد وصول المستخدم**:
* Assign users to either "Retention User" or "Retention Manager" groups
* قم بتعيين المستخدمين إلى مجموعات "مستخدم الاستقطاع" أو "مدير الاستقطاع"
* Managers can approve releases and change configuration
* يمكن للمديرين الموافقة على الإفراجات وتغيير الإعدادات

### 2. Daily Usage / الاستخدام اليومي

**Sales Orders with Retention / أوامر البيع مع الاستقطاع**:
* Create a sales order
* قم بإنشاء أمر بيع
* Go to the Retention tab
* انتقل إلى علامة تبويب الاستقطاع
* Select percentage or fixed amount
* اختر نسبة مئوية أو مبلغ ثابت
* Confirm the order to create a retention record
* قم بتأكيد الطلب لإنشاء سجل استقطاع

**Invoice Handling / معالجة الفواتير**:
* When creating invoices from sales orders, retention is automatically applied
* عند إنشاء فواتير من أوامر البيع، يتم تطبيق الاستقطاع تلقائيًا
* Validate the invoice to hold the retention amount
* قم بالتحقق من صحة الفاتورة لاحتجاز مبلغ الاستقطاع

**Managing Retentions / إدارة الاستقطاعات**:
* View all retentions at Retention → Retentions
* عرض جميع الاستقطاعات في الاستقطاع ← الاستقطاعات
* Filter by status, customer, or date
* تصفية حسب الحالة أو العميل أو التاريخ
* Release retentions in full or partially as needed
* إطلاق الاستقطاعات بالكامل أو جزئيًا حسب الحاجة

**Reporting / إعداد التقارير**:
* Generate retention reports from Retention → Reports
* إنشاء تقارير الاستقطاع من الاستقطاع ← التقارير
* Export to Excel for further analysis
* تصدير إلى Excel لمزيد من التحليل
* Set up automated email reports for finance team
* إعداد تقارير بريد إلكتروني آلية لفريق المالية

### 3. Advanced Features / الميزات المتقدمة

**Automated Releases / الإفراجات الآلية**:
* Enable auto-release in settings for predictable retention periods
* تمكين الإفراج التلقائي في الإعدادات لفترات استقطاع يمكن التنبؤ بها
* The system will automatically generate release entries when due
* سيقوم النظام تلقائيًا بإنشاء إدخالات الإفراج عند استحقاقها

**Customer-Specific Rules / قواعد خاصة بالعملاء**:
* Set up different retention percentages for different customers
* إعداد نسب استقطاع مختلفة لعملاء مختلفين
* Create customer agreement templates with standard terms
* إنشاء قوالب اتفاقيات العملاء مع شروط قياسية

**Multi-Company Support / دعم الشركات المتعددة**:
* If ArabInk has multiple companies, configure separate retention settings for each
* إذا كان لدى حبر العرب التجارية شركات متعددة، قم بتكوين إعدادات استقطاع منفصلة لكل منها
* Each company can have its own retention accounts and rules
* يمكن أن يكون لكل شركة حساباتها وقواعدها الخاصة بالاستقطاع

### 4. Support and Maintenance / الدعم والصيانة

* **First-level support / الدعم من المستوى الأول**: Train key accounting users to handle common questions
* تدريب مستخدمي المحاسبة الرئيسيين للتعامل مع الأسئلة الشائعة
* **Technical issues / المشكلات التقنية**: Set up a support email at ArabInk IT department
* إعداد بريد إلكتروني للدعم في قسم تكنولوجيا المعلومات في حبر العرب التجارية
* **Future enhancements / التحسينات المستقبلية**: Document any customization requests for future updates
* توثيق أي طلبات تخصيص للتحديثات المستقبلية

The module is fully configured for ArabInk's use with comprehensive documentation. Your finance and sales teams will find it intuitive and valuable for managing customer retentions throughout the project lifecycle.
تم تكوين الوحدة بالكامل لاستخدام حبر العرب التجارية مع وثائق شاملة. سيجد فريقا المالية والمبيعات لديك أنها بديهية وقيمة لإدارة استقطاعات العملاء طوال دورة حياة المشروع.
    ''',
    'author':  'Arab ink for trade Eng. Mazin Abdalla',
    'website': 'https://www.arab-ink.com',
    'depends': [
        'base',
        'sale_management',
        'account',
        'product',
        'mail',
        'report_xlsx'
    ],
    'data': [
        'security/retention_security.xml',
        'security/ir.model.access.csv',
        'data/retention_sequence.xml',
        'data/retention_data.xml',
        # Wizards first
        'wizards/retention_release_views.xml',
        # Base views with menu structure
        'views/retention_views.xml',
        # Other views and wizards that use the menu structure
        'wizards/retention_report_wizard_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'reports/retention_report_views.xml',
        'reports/retention_report_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}