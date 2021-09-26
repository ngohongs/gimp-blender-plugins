#include <libgimp/gimp.h>
#include <libgimp/gimpui.h>

static void query       (void);
static void run         (const gchar      *name,
                         gint              nparams,
                         const GimpParam  *param,
                         gint             *nreturn_vals,
                         GimpParam       **return_vals);


static void inverse     (GimpDrawable     *drawable);



GimpPlugInInfo PLUG_IN_INFO =
{
  NULL,  //init
  NULL,  //quit
  query,
  run
};

MAIN()

static void query (void)
{
  static GimpParamDef args[] =
  {
    {
      GIMP_PDB_INT32,
      "run-mode",
      "Run mode"
    },
    {
      GIMP_PDB_IMAGE,
      "image",
      "Input image"
    },
    {
      GIMP_PDB_DRAWABLE,
      "drawable",
      "Input drawable"
    }
  };

  gimp_install_procedure (
    "plug-in-inverse-1-fast-fix",
    "Inverse rychlejsi s opravou (bez nahledu)",
    "Invertuje obrazek",
    "Jiri Chludil",
    "Copyright Jiri Chludil",
    "2016",
    "_Inverse 1 rychlejsi s opravou (bez nahledu)...",
    "RGB*, GRAY*",
    GIMP_PLUGIN,
    G_N_ELEMENTS (args), 0,
    args, NULL);

   gimp_plugin_menu_register ("plug-in-inverse-1-fast-fix","<Image>/Filters/Misc");
}

static void
      run (const gchar      *name,
           gint              nparams,
           const GimpParam  *param,
           gint             *nreturn_vals,
           GimpParam       **return_vals)
      {
        static GimpParam  values[1];
        GimpPDBStatusType status = GIMP_PDB_SUCCESS;
        GimpRunMode       run_mode;
        GimpDrawable     *drawable;

        /* Setting mandatory output values */
        *nreturn_vals = 1;
        *return_vals  = values;

        values[0].type = GIMP_PDB_STATUS;
        values[0].data.d_status = status;

        //ziskani modu 
        run_mode = param[0].data.d_int32;

        //ziskani obrazu 
        drawable = gimp_drawable_get (param[2].data.d_drawable);

        gimp_progress_init ("Negace obrazu...");

        // inverze 
        inverse (drawable);

        // uvolneni obrazu
        gimp_displays_flush ();
        gimp_drawable_detach (drawable);
      }


static void
      inverse (GimpDrawable *drawable)
      {
        // pomocne promenne
        gint         i, j, k, channels;
        // souradnice 
        gint         x1, y1, x2, y2;
        // vstupni a vystupni region  
        GimpPixelRgn rgn_in, rgn_out;
        // reprezentace pixelu   
        guchar       output[4];
        // nacitaci radek a vystupni radek
        guchar       *row, *outrow;
   
        // ziskame souradnice leveho horniho a praveho dolniho rohu obrazku   
        gimp_drawable_mask_bounds (drawable->drawable_id, &x1, &y1, &x2, &y2);
        
        // pocet kanalu
        channels = gimp_drawable_bpp (drawable->drawable_id);

        // nacteni vstupniho regionu
        gimp_pixel_rgn_init (&rgn_in,  drawable, x1, y1, x2 - x1, y2 - y1, FALSE, FALSE);
        
        // nacteni vystupniho regionu
        gimp_pixel_rgn_init (&rgn_out, drawable, x1, y1, x2 - x1, y2 - y1,  TRUE,  TRUE);

        // alokace pameti pro nacitani radku a vystupniho radku
        row = g_new (guchar, channels * (x2 - x1));
        outrow = g_new (guchar, channels * (x2 - x1));

        for (i = y1; i < y2; i++) {
            gimp_pixel_rgn_get_row(&rgn_in, row, x1, i, x2 - x1);
            for (j = x1; j < x2; j++) {
                for (k = 0; k < channels; k++) {
                    outrow[channels * (j - x1) + k] = 255 - row[channels * (j - x1) + k];
                }
            }
            gimp_pixel_rgn_set_row(&rgn_out, outrow, x1, i, x2 - x1);
            if (i % 10 == 0)
              	gimp_progress_update ((gdouble) (i - x1) / (gdouble) (x2 - x1));
        }

        g_free (row);
        g_free (outrow);
        // aktualizace vystupnich dat
        gimp_drawable_flush (drawable);
        gimp_drawable_merge_shadow (drawable->drawable_id, TRUE);
        gimp_drawable_update (drawable->drawable_id, x1, y1, x2 - x1, y2 - y1);
      }

