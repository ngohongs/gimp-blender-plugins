#include <libgimp/gimp.h>
#include <libgimp/gimpui.h>

static void query       (void);
static void run         (const gchar      *name,
                         gint              nparams,
                         const GimpParam  *param,
                         gint             *nreturn_vals,
                         GimpParam       **return_vals);


static void AddColor        (GimpDrawable     *drawable, GimpPreview  *preview);
static gboolean addColor_dialog (GimpDrawable *drawable);

typedef struct
{
  gint     levels[4];
  gboolean preview;
} MyAddColorVals;


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
    "plug-in-addcolor-3",
    "AddColor 3 (s nahledem)",
    "Prida barvu hodnotu k barve",
    "Jiri Chludil",
    "Copyright Jiri Chludil",
    "2016",
    "_AddColor 3 (s nahledem)...",
    "RGB*, GRAY*",
    GIMP_PLUGIN,
    G_N_ELEMENTS (args), 0,
    args, NULL);

  gimp_plugin_menu_register ("plug-in-addcolor-3","<Image>/Filters/Misc");
}

static MyAddColorVals bvals =
{
  50,  /* level */
  0,
  0,
  1,   /* preview */
};


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
        gint     channels;

        /* Setting mandatory output values */
        *nreturn_vals = 1;
        *return_vals  = values;

        values[0].type = GIMP_PDB_STATUS;
        values[0].data.d_status = status;

        //ziskani modu 
        run_mode = param[0].data.d_int32;

        //ziskani obrazu 
        drawable = gimp_drawable_get (param[2].data.d_drawable);

        channels = gimp_drawable_bpp (drawable->drawable_id);

        switch (run_mode)
        {
          case GIMP_RUN_INTERACTIVE:
            /* Get options last values if needed */
            gimp_get_data ("plug-in-addcolor-3", &bvals);

            /* Display the dialog */
            if (! addColor_dialog (drawable))
              return;
            break;

          case GIMP_RUN_NONINTERACTIVE:
            switch (channels) 
            {
              case 1:
                if (nparams != 4)
                 status = GIMP_PDB_CALLING_ERROR;
                if (status == GIMP_PDB_SUCCESS)
                  bvals.levels[0] = param[3].data.d_int32;
                break;
              case 2:
                if (nparams != 5)
                 status = GIMP_PDB_CALLING_ERROR;
                if (status == GIMP_PDB_SUCCESS) 
                {
                  bvals.levels[0] = param[3].data.d_int32;
                  bvals.levels[3] = param[4].data.d_int32;
                }
                break;
              case 3:
                if (nparams != 6)
                 status = GIMP_PDB_CALLING_ERROR;
                if (status == GIMP_PDB_SUCCESS) 
                {
                  bvals.levels[0] = param[3].data.d_int32;
                  bvals.levels[1] = param[4].data.d_int32;
                  bvals.levels[2] = param[5].data.d_int32;
                }
                break;
              case 4:
                if (nparams != 7)
                 status = GIMP_PDB_CALLING_ERROR;
                if (status == GIMP_PDB_SUCCESS) 
                {
                  bvals.levels[0] = param[3].data.d_int32;
                  bvals.levels[1] = param[4].data.d_int32;
                  bvals.levels[2] = param[5].data.d_int32;
                  bvals.levels[3] = param[6].data.d_int32;
                }
                break;
              default:
                break;
            }
          case GIMP_RUN_WITH_LAST_VALS:
            /*  Get options last values if needed  */
            gimp_get_data ("plug-in-addcolor-3", &bvals);
            break;

          default:
            break;
	      }
	       

        gimp_progress_init ("Posun kanalu...");

        // inverze 
        AddColor (drawable, NULL);

        // uvolneni obrazu
        gimp_displays_flush ();
        gimp_drawable_detach (drawable);

        if (run_mode == GIMP_RUN_INTERACTIVE)
          gimp_set_data ("plug-in-addcolor-3", &bvals, sizeof (MyAddColorVals) );

        return;
      }


static void
      AddColor (GimpDrawable *drawable, GimpPreview  *preview)
      {
        // pomocne promenne
        gint         i, j, k, channels, width, height;
        // souradnice 
        gint         x1, y1, x2, y2;
        // vstupni a vystupni region  
        GimpPixelRgn rgn_in, rgn_out;
        // reprezentace radku   
        guchar      *inrow, *outrow;
        
        if (preview) {
              gimp_preview_get_position (preview, &x1, &y1);
              gimp_preview_get_size (preview, &width, &height);
              x2 = x1 + width;
              y2 = y1 + height;
            }
        else
            {
                    // ziskame souradnice leveho horniho a praveho dolniho rohu obrazku   
              gimp_drawable_mask_bounds (drawable->drawable_id,
                                  &x1, &y1,
                                  &x2, &y2);
              width = x2 - x1;
              height = y2 - y1;
            }



        // pocet kanalu
        channels = gimp_drawable_bpp (drawable->drawable_id);

        // nacteni vstupniho regionu
        gimp_pixel_rgn_init (&rgn_in,  drawable, x1, y1, x2 - x1, y2 - y1, FALSE, FALSE);
        
        // nacteni vystupniho regionu
        gimp_pixel_rgn_init (&rgn_out, drawable, x1, y1, x2 - x1, y2 - y1,  TRUE,  TRUE);


        inrow = g_new (guchar, width * channels);
        outrow = g_new (guchar, width * channels);
        for (i = y1; i < y2; i++) {
            gimp_pixel_rgn_get_row (&rgn_in, inrow, x1, i, width);
            for (j = 0; j < width; j++) {
                // konverze
                for (k = 0; k < channels; k++)
                {
                  outrow[j*channels+k] = CLAMP(inrow[j*channels+k] + bvals.levels[k],0,255);
                }

            }

            gimp_pixel_rgn_set_row (&rgn_out, outrow, x1, i , width);
  
            // aktualizace progress baru
            if (i % 10 == 0)
              	gimp_progress_update ((gdouble) (i - x1) / (gdouble) (x2 - x1));
          }
        g_free (inrow);
        g_free (outrow);

	if (preview) {
		gimp_drawable_preview_draw_region (GIMP_DRAWABLE_PREVIEW (preview),&rgn_out);
	}
	else
	{
		// aktualizace vystupnich dat
		gimp_drawable_flush (drawable);
		gimp_drawable_merge_shadow (drawable->drawable_id, TRUE);
		gimp_drawable_update (drawable->drawable_id, x1, y1, x2 - x1, y2 - y1);
	}
}

static gboolean addColor_dialog (GimpDrawable *drawable)
{
  gint channels;
  GtkWidget *dialog;
  GtkWidget *main_vbox;
  GtkWidget *main_hbox;
  GtkWidget *preview;
  GtkWidget *frame;
  GtkWidget *radius_label;
  GtkWidget *alignment;
  GtkWidget *spinbutton;
  GtkObject *spinbutton_adj;
  GtkWidget *spinbutton1;
  GtkObject *spinbutton1_adj;
  GtkWidget *spinbutton2;
  GtkObject *spinbutton2_adj;
  GtkWidget *spinbutton3;
  GtkObject *spinbutton3_adj;
  GtkWidget *level_label;
  GtkWidget *frame_label;  
  gboolean   run;
  
  gimp_ui_init ("addcolor", FALSE);

  channels = gimp_drawable_bpp (drawable->drawable_id);

  dialog = gimp_dialog_new ("Posun kanalu", "posun kanalu",
                            NULL, 0,
                            gimp_standard_help_func, "plug-in-addcolor-3",

                            GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL,
                            GTK_STOCK_OK,     GTK_RESPONSE_OK,

                            NULL);

  main_vbox = gtk_vbox_new (FALSE, 6);
  gtk_container_add (GTK_CONTAINER (GTK_DIALOG (dialog)->vbox), main_vbox);
  gtk_widget_show (main_vbox);

  preview = gimp_drawable_preview_new (drawable,&bvals.preview);
  gtk_box_pack_start (GTK_BOX (main_vbox), preview, TRUE, TRUE, 0);
  gtk_widget_show (preview);

  frame = gtk_frame_new ("Hello");
  gtk_box_pack_start (GTK_BOX (main_vbox), frame, TRUE, TRUE, 0);
  gtk_widget_show (frame);
  // gtk_container_set_border_width (GTK_CONTAINER (frame), 6);

  alignment = gtk_alignment_new (0.5, 0.5, 1, 1);
  gtk_widget_show (alignment);
  gtk_container_add (GTK_CONTAINER (frame), alignment);
  gtk_alignment_set_padding (GTK_ALIGNMENT (alignment), 6, 6, 6, 6);

  main_hbox = gtk_hbox_new (FALSE, 12);
  gtk_container_set_border_width( GTK_CONTAINER (main_hbox), 12);
  gtk_widget_show (main_hbox);
  gtk_container_add (GTK_CONTAINER (alignment), main_hbox);

  level_label = gtk_label_new_with_mnemonic ("_Level:");
  gtk_widget_show (level_label);
  gtk_box_pack_start (GTK_BOX (main_hbox), level_label, FALSE, FALSE, 6);
  gtk_label_set_justify (GTK_LABEL (level_label), GTK_JUSTIFY_RIGHT);

  switch (channels) 
  {
    case 1:
      spinbutton = gimp_spin_button_new (&spinbutton_adj, bvals.levels[0], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton);
      break;
    case 2:
      spinbutton = gimp_spin_button_new (&spinbutton_adj, bvals.levels[0], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton);

      spinbutton1 = gimp_spin_button_new (&spinbutton1_adj, bvals.levels[3], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton1, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton1);
      break;
    case 3:
      spinbutton = gimp_spin_button_new (&spinbutton_adj, bvals.levels[0], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton);

      spinbutton1 = gimp_spin_button_new (&spinbutton1_adj, bvals.levels[1], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton1, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton1);

      spinbutton2 = gimp_spin_button_new (&spinbutton2_adj, bvals.levels[2], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton2, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton2);
      break;
    case 4:
      spinbutton = gimp_spin_button_new (&spinbutton_adj, bvals.levels[0], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton);

      spinbutton1 = gimp_spin_button_new (&spinbutton1_adj, bvals.levels[1], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton1, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton1);

      spinbutton2 = gimp_spin_button_new (&spinbutton2_adj, bvals.levels[2], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton2, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton2);

      spinbutton3 = gimp_spin_button_new (&spinbutton3_adj, bvals.levels[3], -255, 255, 1, 1, 1, 5, 0);
      gtk_box_pack_start (GTK_BOX (main_hbox), spinbutton3, FALSE, FALSE, 0);
      gtk_widget_show (spinbutton3);
      break;
    default:
      break;
  }

  frame_label = gtk_label_new ("<b>Modify level</b>");
  gtk_widget_show (frame_label);
  gtk_frame_set_label_widget (GTK_FRAME (frame), frame_label);
  gtk_label_set_use_markup (GTK_LABEL (frame_label), TRUE);

  g_signal_connect_swapped (preview, "invalidated",
                            G_CALLBACK (AddColor),
                            drawable);
  switch(channels)
  {
    case 1:
      g_signal_connect_swapped (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      break;
    case 2:
      g_signal_connect_swapped (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      g_signal_connect_swapped (spinbutton3_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      break;  
    case 3:
      g_signal_connect_swapped (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      g_signal_connect_swapped (spinbutton1_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      g_signal_connect_swapped (spinbutton2_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      break;
    case 4:
      g_signal_connect_swapped (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      g_signal_connect_swapped (spinbutton1_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      g_signal_connect_swapped (spinbutton2_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      g_signal_connect_swapped (spinbutton3_adj, "value_changed",
                      G_CALLBACK (gimp_preview_invalidate),
                      preview);
      break;
    default:
      break;
  }

  AddColor (drawable, GIMP_PREVIEW (preview));

  switch(channels)
  {
    case 1:
      g_signal_connect (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels);
      break;
    case 2:
      g_signal_connect (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels);
      g_signal_connect (spinbutton3_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels+3);
      break;  
    case 3:
      g_signal_connect (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels);
      g_signal_connect (spinbutton1_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels+1);
      g_signal_connect (spinbutton2_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels+2);
      break;
    case 4:
      g_signal_connect (spinbutton_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels);
      g_signal_connect (spinbutton1_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels+1);
      g_signal_connect (spinbutton2_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels+2);
      g_signal_connect (spinbutton3_adj, "value_changed",
                      G_CALLBACK (gimp_int_adjustment_update),
                      bvals.levels+3);
      break;
    default:
      break;
  }
  gtk_widget_show (dialog);

  run = (gimp_dialog_run (GIMP_DIALOG (dialog)) == GTK_RESPONSE_OK);

  gtk_widget_destroy (dialog);

  return run;
}

