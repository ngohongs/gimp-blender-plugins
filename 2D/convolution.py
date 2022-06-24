#!/usr/bin/env python
# -*- coding: utf-8 -*-
import array, sys, json

import numpy as np
import cv2

import gimp, gimpplugin
from gimpenums import *
import gtk, gimpui, gimpcolor
from gimpshelf import shelf

# console output for debugging
# sys.stdout = open("PATH TO THE OUTPUT FILE", 'w')
# sys.stderr = sys.stdout 


def clamp(val, low, high):
    return max(min(high, val), low)


class filter_plugin(gimpplugin.plugin):
    shelfkey = "convolution_shelf_key"
    
    # convolution edge handling
    # each border type handling explained:
    # https://vovkos.github.io/doxyrest-showcase/opencv/sphinx_rtd_theme/enum_cv_BorderTypes.html
    edge_type = {
        0: cv2.BORDER_REFLECT_101,
        1: cv2.BORDER_REPLICATE,
        2: cv2.BORDER_REFLECT,
        3: cv2.BORDER_ISOLATED
    }

    def convolve(self, work_pixels):
        """
        Generic convolution filter

        accepts work_pixels in format of cv2 image numpy array
        """
        return cv2.filter2D(work_pixels, -1, self.kernel_param, borderType=self.edge_param)

    def box_blur(self, work_pixels):
        """
        Box blur filter 

        average from the square (2 * int(self.radius_param) + 1) x (2 * int(self.radius_param) + 1)
        """
        s = 2 * int(self.radius_param) + 1
        self.kernel_param = np.ones((s,s)) / (s * s)
        return self.convolve(work_pixels)

    def gaussian_blur(self, work_pixels):
        """
        Gaussian blur 

        blurs work_image (image in cv2 format numpy array) with gaussian kernel with size (2 * int(self.radius_param) + 1)
        """
        s = 2 * int(self.radius_param) + 1
        return cv2.GaussianBlur(work_pixels, (s, s), 0, borderType=self.edge_param)

    def gaussian_sharpen(self, work_pixels):
        """
        Gaussian sharpen

        inspired by https://www.websupergoo.com/helpie/default.htm?page=source%2F2-effects%2Funsharpmask.htm

        sharpens the image by adding the difference of the original image and gaussian blurred image only when the difference exceeds the threshold  
        """
        blur = self.gaussian_blur(np.copy(work_pixels)).astype(np.uint8)
        shape = work_pixels.shape
        for x in range(shape[0]):
            for y in range(shape[1]):
                for z in range(shape[2]):
                    if clamp(int(work_pixels[x,y,z]) - int(blur[x,y,z]), 0, 255) > self.threshold_param:
                        work_pixels[x,y,z] = clamp(2 * int(work_pixels[x,y,z]) - int(blur[x,y,z]), 0, 255)
        return work_pixels
    
    def sharpen(self, work_pixels):
        """
        Sharpen 

        sharpens the image by adding edge detected image self.radius_param times
        """

        identity = np.array([[0,0,0],[0,1,0],[0,0,0]])
        edge_detection = np.array([[0,-1,0],[-1,4,-1],[0,-1,0]])
        self.kernel_param = identity + self.radius_param * edge_detection
        return self.convolve(work_pixels)
    
    def pixelate(self, work_pixels):
        """
        Pixelation

        pixelates the image by resizing the original image down to (imageSize / self.radius_param) with linear interpolation
        and then rescale it back to the original size with nearest interpolation
        """
        shape = work_pixels.shape
        nw = int(shape[1] / self.radius_param)
        nh = int(shape[0] / self.radius_param)
        temp = cv2.resize(work_pixels, (nw, nh), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(temp, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)

    def shelf_store(self, filter=0, radius=1, edge=0, threshold=1, kernel="[[0,0,0],[0,1,0],[0,0,0]]"):
        """
        Help function for storing last values for run mode RUN_WITH_LAST_VALS
        """
        shelf[filter_plugin.shelfkey] = {
                "filter":    filter,
                "radius":    radius,
                  "edge":    edge,
             "threshold":    threshold,
                "kernel":    kernel
            }
    
    def param_retrieve(self, filter=0, radius=1, edge=0, threshold=1, kernel="[[0,0,0],[0,1,0],[0,0,0]]"):
        """
        Input retrieval and input validation
        """
        if self.run_mode == RUN_INTERACTIVE:
            self.filter_param = self.combobox_filter.get_active()
            self.radius_param = self.radius_spin.get_value()
            self.threshold_param = self.threshold.get_value()
            # self.edge_param = self.edge_param
            self.text_param = self.textbox.get_text()
        elif self.run_mode == RUN_NONINTERACTIVE:
            if 0 > filter or filter > 5:
                return -1
            if 1 > radius or radius > 1024:
                return -1
            if 0 > edge or edge > 3:
                return -1
            if 1 > threshold or threshold > 255:
                return -1 
            self.filter_param = filter
            self.radius_param = radius
            self.edge_param = filter_plugin.edge_type[edge]
            self.threshold_param = threshold
            self.text_param = kernel
        elif self.run_mode == RUN_WITH_LAST_VALS:
            self.filter_param = shelf[filter_plugin.shelfkey]["filter"]
            self.radius_param = shelf[filter_plugin.shelfkey]["radius"]
            self.edge_param = shelf[filter_plugin.shelfkey]["edge"]
            self.threshold_param = shelf[filter_plugin.shelfkey]["threshold"]
            self.text_param = shelf[filter_plugin.shelfkey]["kernel"]
        if self.filter_param == 5:
            try:
                tmp = json.loads(self.text_param)
                custom_kernel = np.array(tmp)
            except:
                return -1
            shape = custom_kernel.shape
            if len(shape) == 2 and shape[0] == shape[1] and shape[0] % 2 == 1:
                self.kernel_param = custom_kernel
            else:
                return -1

        self.shelf_store(self.filter_param, 
                         self.radius_param, 
                         self.edge_param, 
                         self.threshold_param, 
                         self.text_param)
        return 0          
            
    def filter_select(self, combobox_filter):
        """
        Help function for filter combo box 

        disables widgets according to selected filter
        """
        case = combobox_filter.get_active()
        if case == 0:
            self.radius_spin.set_sensitive(True)
            self.combobox_edge.set_sensitive(True)
            self.threshold.set_sensitive(False)
            self.textbox.set_sensitive(False)
        elif case == 1:
            self.radius_spin.set_sensitive(True)
            self.combobox_edge.set_sensitive(True)
            self.threshold.set_sensitive(False)
            self.textbox.set_sensitive(False)
        elif case == 2:
            self.radius_spin.set_sensitive(True)
            self.combobox_edge.set_sensitive(True)
            self.threshold.set_sensitive(True)
            self.textbox.set_sensitive(False)
        elif case == 3:
            self.radius_spin.set_sensitive(True)
            self.combobox_edge.set_sensitive(True)
            self.threshold.set_sensitive(False)
            self.textbox.set_sensitive(False)
        elif case == 4:
            self.radius_spin.set_sensitive(True)
            self.combobox_edge.set_sensitive(False)
            self.threshold.set_sensitive(False)
            self.textbox.set_sensitive(False)
        elif case == 5:
            self.radius_spin.set_sensitive(False)
            self.combobox_edge.set_sensitive(True)
            self.threshold.set_sensitive(False)
            self.textbox.set_sensitive(True)
            
    
    def edge_select(self, combobox_edge):
        """
        Help function for edge handling combo box
        """
        case = combobox_edge.get_active()
        self.edge_param = filter_plugin.edge_type[case]

    def create_warning_dialog(self):
        """
        Warning dialog creation
        """
        self.warn_dialog = gtk.MessageDialog(self.dialog, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
        gtk.BUTTONS_CLOSE, "Incorrect kernel format")
        print("[ERROR]: Incorrect kernel format")
        self.warn_dialog.run()

    def apply_filter(self):
        """
        Filter application 

        applies selected filter onto the image
        """
        gimp.progress_init('Convolution')

        # gimp input
        gimp.progress_update(0.1)
        bpp = self.drawable.bpp
        (bx1, by1, bx2, by2) = self.drawable.mask_bounds
        bw = bx2 - bx1
        bh = by2 - by1

        
        # input retrieval
        gimp.progress_update(0.2)
        src_rgn = self.drawable.get_pixel_rgn(bx1, by1, bw, bh, False, False)
        src_pixels = array.array("B", src_rgn[bx1:bx2, by1:by2])

        # output
        gimp.progress_update(0.3)
        dst_rgn = self.drawable.get_pixel_rgn(bx1, by1, bw, bh, True, True)

        # filter application
        gimp.progress_update(0.4)
        work_pixels = np.reshape(src_pixels,(bh,bw,bpp)).astype(np.uint8)
        
        gimp.progress_update(0.5)
        if self.filter_param == 0:
            result_pixels = self.box_blur(work_pixels)
        elif self.filter_param == 1:
            result_pixels = self.gaussian_blur(work_pixels)
        elif self.filter_param == 2:
            result_pixels = self.gaussian_sharpen(work_pixels)
        elif self.filter_param == 3:
            result_pixels = self.sharpen(work_pixels)
        elif self.filter_param == 4:
            result_pixels = self.pixelate(work_pixels)
        elif self.filter_param == 5:
            result_pixels = self.convolve(work_pixels)
        else:
            result_pixels = work_pixels

        #output write
        gimp.progress_update(0.9)
        dst_rgn[bx1:bx2, by1:by2] = result_pixels.tostring()
        self.drawable.merge_shadow(True)
        self.drawable.update(bx1,by1,bw,bh)
        gimp.displays_flush()

    def ok_clicked(self, button):
        """
        Help function for OK button in the main dialog
        """
        if self.param_retrieve() == 0:
            self.apply_filter()
        elif self.run_mode == RUN_INTERACTIVE:
            self.create_warning_dialog()

    def create_dialog(self):
        self.dialog = gimpui.Dialog("Convolution", "covolution_dialog")

        # 4x4 homogenous table
        self.table = gtk.Table(6, 7, False)
        self.table.set_row_spacings(8)
        self.table.set_col_spacings(8)
        self.table.show()

        # arrange horizontally
        self.dialog.vbox.hbox1 = gtk.HBox(True, 0)
        self.dialog.vbox.hbox1.show()
        self.dialog.vbox.pack_start(self.dialog.vbox.hbox1, False, False, 0)
        self.dialog.vbox.hbox1.pack_start(self.table, True, True, 0)

        # filter label
        self.label_filter = gtk.Label("Filter:")
        self.label_filter.show()
        self.table.attach(self.label_filter, 1, 2, 1, 2)

        # radius label
        self.label_radius = gtk.Label("Radius:")
        self.label_radius.show()
        self.table.attach(self.label_radius, 1, 2, 2, 3)

        # radius spin button
        self.radius_adj = gtk.Adjustment(1.0, 1.0, 1024.0, 1.0, 5.0, 0.0)
        self.radius_spin = gtk.SpinButton(self.radius_adj, 0, 0)
        self.radius_spin.set_wrap(True)
        self.radius_spin.show()
        self.table.attach(self.radius_spin, 2, 3, 2, 3)

        # threshold label
        self.label_thres = gtk.Label("Threshold:")
        self.label_thres.show()
        self.table.attach(self.label_thres, 1, 2, 6, 7)

        # threshold level
        self.threshold_adj = gtk.Adjustment(1.0, 0.0, 255.0, 1.0, 1.0, 0)
        self.threshold = gtk.HScale(self.threshold_adj)
        self.threshold.set_digits(0)
        self.threshold.set_value(1)
        self.threshold.show()
        self.table.attach(self.threshold, 2, 3, 6, 7)
        
        # custom kernel label
        self.label_custom = gtk.Label("Custom kernel:")
        self.label_custom.show()
        self.table.attach(self.label_custom, 1, 2, 7, 8)

        # custom kernel
        self.textbox = gtk.Entry()
        self.textbox.show()
        self.table.attach(self.textbox, 2, 3, 7, 8)

        # edge handling
        self.label_edge = gtk.Label("Edge handling:")
        self.label_edge.show()
        self.table.attach(self.label_edge, 1, 2, 4, 5)

        # drop down menu for choice of edge handling
        self.combobox_edge = gtk.combo_box_new_text()
        self.combobox_edge.append_text("Reflect 101")
        self.combobox_edge.append_text("Replicate")
        self.combobox_edge.append_text("Reflect")
        self.combobox_edge.append_text("Isolated")
        self.combobox_edge.connect("changed", self.edge_select)
        self.combobox_edge.set_entry_text_column(0)
        self.combobox_edge.set_active(0)
        self.combobox_edge.show()
        self.table.attach(self.combobox_edge, 2, 3, 4, 5)

        # drop down menu for choice of filters
        self.combobox_filter = gtk.combo_box_new_text()
        self.combobox_filter.append_text("Box Blur")
        self.combobox_filter.append_text("Gaussian Blur")
        self.combobox_filter.append_text("Gaussian Sharpen")
        self.combobox_filter.append_text("Sharpen")
        self.combobox_filter.append_text("Pixelate")
        self.combobox_filter.append_text("Custom kernel")
        self.combobox_filter.connect("changed", self.filter_select)
        self.combobox_filter.set_entry_text_column(0)
        self.combobox_filter.set_active(0)
        self.combobox_filter.show()
        self.table.attach(self.combobox_filter, 2, 3, 1, 2)

        # dialog buttons
        self.cancel_button = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.ok_button = self.dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.ok_button.connect("clicked", self.ok_clicked)

    def convolution_plugin_main(self, run_mode, image, drawable, *args):
        """
        Main function of the plugin
        """
        self.run_mode = run_mode
        self.image = image
        self.drawable = drawable
        self.create_dialog()

        # save default values for the filter if not set
        if not shelf.has_key(filter_plugin.shelfkey):
            self.shelf_store()

        if run_mode == RUN_INTERACTIVE:
            self.dialog.run()
        elif run_mode == RUN_NONINTERACTIVE:
            if self.param_retrieve(args[0], args[1], args[2], args[3], args[4]) == 0:
                print(args)
                self.apply_filter()
            else:
                print("[ERROR]: Incorrect input format for this type of filter")
        elif run_mode == RUN_WITH_LAST_VALS:
            self.ok_clicked(None)
   
    def init(self):
        pass

    def quit(self):
        pass
    
    def query(self):
        gimp.install_procedure(
            "convolution_plugin_main",
            "Convolution filter",
            "Convolution operator with the options of Gaussian blur, Gaussian sharpening, unsharpen and pixelization",
            "Hong Son Ngo",
            "Hong Son Ngo",
            "2021",
            "<Image>/_Plugins/Convolution",
            "RGB*, GRAY*",
            PLUGIN,
            [  # next three parameters are common for all scripts that are inherited from gimpplugin.plugin
                (PDB_INT32, "run_mode", "Run mode"),
                (PDB_IMAGE, "image", "Input image"),
                (PDB_DRAWABLE, "drawable", "Input drawable"),
                # custom parameters
                (PDB_INT32, "filter", "Filter type"),
                (PDB_INT32, "radius", "Radius parameter"),
                (PDB_INT32, "edge", "Edge case handling type"),
                (PDB_INT32, "threshold", "Threshold for Gaussian Sharpening"),
                (PDB_STRING, "kernel", "Custom kernel")
            ],
            []
        )

    def start(self):
        gimp.main(self.init, self.quit, self.query, self._run)


if __name__ == '__main__':
    filter_plugin().start()
