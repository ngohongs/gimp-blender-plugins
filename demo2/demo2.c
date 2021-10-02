#include <libgimp/gimp.h>
#include <libgimp/gimpui.h>

static void query       (void);
static void run         (const gchar      *name,
                         gint              nparams,
                         const GimpParam  *param,
                         gint             *nreturn_vals,
                         GimpParam       **return_vals);


static void inverse        (GimpDrawable     *drawable);
static void addColor       (GimpDrawable     *drawable, int level);
static gboolean addColor_dialog ();



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
    "plug-in-add-color",
    "Posun kanalu (s nahledem)",
    "Posune barvne kanaly obrazku",
    "Jiri Chludil",
    "Copyright Jiri Chludil",
    "2021",
    "_Posun kanalu (s nahledem)...",
    "RGB*, GRAY*",
    GIMP_PLUGIN,
    G_N_ELEMENTS (args), 0,
    args, NULL);

  gimp_plugin_menu_register ("plug-in-add-color","<Image>/Filters/Misc");
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

      if (!addColor_dialog()) {
        return; 
      }

        gimp_progress_init ("Posune kanaly obrazku...");

        addColor (drawable, 42);

        // uvolneni obrazu
        gimp_displays_flush ();
        gimp_drawable_detach (drawable);
      }


static void
      addColor (GimpDrawable *drawable, int level)
      {
        // pomocne promenne
        gint         i, j, k, channels, width;
        // souradnice 
        gint         x1, y1, x2, y2;
        // vstupni a vystupni region  
        GimpPixelRgn rgn_in, rgn_out;
        // reprezentace radku   
        guchar      *inrow, *outrow;
   
        // ziskame souradnice leveho horniho a praveho dolniho rohu obrazku   
        gimp_drawable_mask_bounds (drawable->drawable_id, &x1, &y1, &x2, &y2);
        
        // pocet kanalu
        channels = gimp_drawable_bpp (drawable->drawable_id);

        // nacteni vstupniho regionu
        gimp_pixel_rgn_init (&rgn_in,  drawable, x1, y1, x2 - x1, y2 - y1, FALSE, FALSE);
        
        // nacteni vystupniho regionu
        gimp_pixel_rgn_init (&rgn_out, drawable, x1, y1, x2 - x1, y2 - y1,  TRUE,  TRUE);


        width = x2 - x1;
        inrow = g_new (guchar, width * channels);
        outrow = g_new (guchar, width * channels);
        for (i = y1; i < y2; i++) {
            gimp_pixel_rgn_get_row (&rgn_in, inrow, x1, i, width);
            for (j = 0; j < width; j++) {
                // konverze
                for (k = 0; k < channels; k++)
                {
                    outrow[j*channels+k] =  CLAMP(inrow[j*channels+k]+level,0,255);
                }
            }
            gimp_pixel_rgn_set_row (&rgn_out, outrow, x1, i , width);
  
            // aktualizace progress baru
            if (i % 10 == 0)
              	gimp_progress_update ((gdouble) (i - x1) / (gdouble) (x2 - x1));
          }
        g_free (inrow);
        g_free (outrow);

        // aktualizace vystupnich dat
        gimp_drawable_flush (drawable);
        gimp_drawable_merge_shadow (drawable->drawable_id, TRUE);
        gimp_drawable_update (drawable->drawable_id, x1, y1, x2 - x1, y2 - y1);
      }

static gboolean addColor_dialog () {
  GtkWidget* dialog;
  gboolean run;

  gimp_ui_init("add-color", FALSE);
  dialog = gimp_dialog_new("Posun kanalu", "add-color", NULL, 0, gimp_standard_help_func, "plugin-add-color",
     GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL, GTK_STOCK_OK, GTK_RESPONSE_OK, NULL);

  gtk_widget_show(dialog);
  run = gimp_dialog_run(GIMP_DIALOG(dialog)) == GTK_RESPONSE_OK;
  gtk_widget_destroy(dialog);
  return run;
}
